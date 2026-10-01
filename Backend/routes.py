from pathlib import Path
import uuid

from flask import Blueprint, jsonify, request, render_template
import pandas as pd

from Backend.ingestion import save_file, read_csv
from Backend.processing import get_profile, get_raw_missing
from Backend.chunking import create_chunks, create_text
from Backend.embedding import create_embeddings
from Backend.qdrant import store_vectors, clear_collection
from Backend.rag import get_relevant_data
from Backend.classifier import classify_question
from Backend.ai import generate_code, explain_result
from Backend.executor import execute_code
from Backend.database import (
    save_dataset,
    create_session,
    save_query,
    get_history
)

routes = Blueprint("routes", __name__)

current_data = None
current_dataset_id = None
current_session_id = None

# All uploaded files
all_uploaded_files = []


def public_file_info(file_info):
    return {
        "id": file_info["id"],
        "name": file_info["name"],
        "rows": file_info["rows"],
        "columns": file_info["columns"]
    }


def restore_uploaded_files():
    global current_data
    global all_uploaded_files

    if all_uploaded_files:
        return

    upload_dir = Path("Uploads")
    if not upload_dir.is_dir():
        return

    restored_data = []
    for file_path in sorted(upload_dir.glob("*.csv")):
        try:
            data = read_csv(str(file_path))
        except Exception as error:
            print(f"Could not restore {file_path.name}: {error}")
            continue

        stored_name = file_path.name
        prefix, separator, original_name = stored_name.partition("_")
        if (
            separator
            and len(prefix) == 32
            and all(character in "0123456789abcdef" for character in prefix.lower())
        ):
            stored_name = original_name

        all_uploaded_files.append({
            "id": uuid.uuid4().hex,
            "name": stored_name,
            "path": str(file_path),
            "rows": len(data),
            "columns": len(data.columns),
            "schema": list(data.columns)
        })
        restored_data.append(data)

    if restored_data:
        current_data = pd.concat(restored_data, ignore_index=True)


@routes.route("/")
def home():
    return render_template("index.html")


@routes.route("/files")
def files_page():
    restore_uploaded_files()
    return render_template("files.html")


@routes.route("/api/files", methods=["GET"])
def list_uploaded_files():
    restore_uploaded_files()
    return jsonify({
        "files": [public_file_info(file) for file in all_uploaded_files]
    })


@routes.route("/api/profile", methods=["GET"])
def current_profile():
    restore_uploaded_files()

    if current_data is None:
        return jsonify({"profile": None})

    profile = get_profile(
        current_data,
        source_files=all_uploaded_files
    )
    profile["total_files"] = len(all_uploaded_files)
    profile["files"] = [
        public_file_info(file) for file in all_uploaded_files
    ]

    return jsonify({"profile": profile})


@routes.route("/api/files/<file_id>", methods=["DELETE"])
def delete_uploaded_file(file_id):

    global current_data
    global current_dataset_id
    global current_session_id
    global all_uploaded_files

    file_to_remove = next(
        (file for file in all_uploaded_files if file["id"] == file_id),
        None
    )

    if file_to_remove is None:
        return jsonify({"error": "File not found"}), 404

    upload_root = Path("Uploads").resolve()
    file_path = Path(file_to_remove["path"]).resolve()

    if upload_root not in file_path.parents:
        return jsonify({"error": "Invalid upload path"}), 400

    try:
        file_path.unlink(missing_ok=True)
        all_uploaded_files = [
            file for file in all_uploaded_files if file["id"] != file_id
        ]

        remaining_data = [
            read_csv(file["path"])
            for file in all_uploaded_files
            if Path(file["path"]).is_file()
        ]

        current_data = (
            pd.concat(remaining_data, ignore_index=True)
            if remaining_data
            else None
        )
        current_dataset_id = None
        current_session_id = None

        clear_collection("dataset_chunks")

        texts = []
        file_names = []
        for file, data in zip(all_uploaded_files, remaining_data):
            for chunk in create_chunks(data):
                texts.append(create_text(chunk))
                file_names.append(file["name"])

        if texts:
            store_vectors(
                "dataset_chunks",
                create_embeddings(texts),
                texts,
                file_names
            )

        profile = (
            get_profile(current_data, source_files=all_uploaded_files)
            if current_data is not None
            else None
        )
        if profile is not None:
            profile["total_files"] = len(all_uploaded_files)
            profile["files"] = [
                public_file_info(file) for file in all_uploaded_files
            ]

        return jsonify({
            "files": [public_file_info(file) for file in all_uploaded_files],
            "total_files": len(all_uploaded_files),
            "profile": profile
        })

    except Exception as error:
        print("\nFILE DELETE ERROR:")
        print(error)
        return jsonify({"error": str(error)}), 500


@routes.route("/ask-page")
def ask_page():
    return render_template("ask.html")


@routes.route("/history")
def history_page():
    return render_template("history.html")


@routes.route("/upload", methods=["POST"])
def upload_file():

    global current_data
    global current_dataset_id
    global current_session_id
    global all_uploaded_files

    try:
        restore_uploaded_files()

        if "files" in request.files:
            files = request.files.getlist("files")

        elif "file" in request.files:
            files = [request.files["file"]]

        else:
            return jsonify({
                "error": "No file uploaded"
            }), 400

        new_data = []
        new_files = []

        for file in files:

            if not file.filename:
                continue

            if not file.filename.lower().endswith(".csv"):
                continue

            file_path = save_file(file)

            data = read_csv(file_path)

            new_data.append(data)

            file_info = {
                "id": uuid.uuid4().hex,
                "name": file.filename,
                "path": file_path,
                "rows": len(data),
                "columns": len(data.columns),
                "schema": list(data.columns)
            }

            new_files.append(file_info)

        if not new_data:

            return jsonify({
                "error": "No valid CSV files found"
            }), 400

        # ------------------------------------------------
        # ADD NEW DATA TO OLD DATA
        # ------------------------------------------------

        if current_data is None:

            current_data = pd.concat(
                new_data,
                ignore_index=True
            )

        else:

            current_data = pd.concat(
                [current_data] + new_data,
                ignore_index=True
            )

        # Add files to existing file list
        all_uploaded_files.extend(new_files)

        # ------------------------------------------------
        # DATABASE
        # ------------------------------------------------

        first_file = new_files[0]

        current_dataset_id = save_dataset(
            first_file["name"],
            first_file["path"],
            first_file["rows"],
            first_file["columns"]
        )

        current_session_id = create_session(
            current_dataset_id
        )

        # ------------------------------------------------
        # PROFILE
        # ------------------------------------------------

        profile = get_profile(
            current_data,
            source_files=all_uploaded_files
        )

        profile["total_files"] = len(
            all_uploaded_files
        )

        profile["files"] = [
            public_file_info(file) for file in all_uploaded_files
        ]

        # ------------------------------------------------
        # QDRANT / RAG
        # ------------------------------------------------

        texts = []
        vector_file_names = []

        for index, data in enumerate(new_data):

            chunks = create_chunks(data)

            for chunk in chunks:

                texts.append(
                    create_text(chunk)
                )

                vector_file_names.append(
                    new_files[index]["name"]
                )

        if texts:

            vectors = create_embeddings(texts)

            store_vectors(
                "dataset_chunks",
                vectors,
                texts,
                vector_file_names
            )

        # ------------------------------------------------
        # RESPONSE
        # ------------------------------------------------

        return jsonify({

            "message": "Files uploaded successfully",

            "files": [
                public_file_info(file) for file in all_uploaded_files
            ],

            "total_files": len(
                all_uploaded_files
            ),

            "profile": profile

        })

    except Exception as error:

        print("\nUPLOAD ERROR:")
        print(error)

        return jsonify({
            "error": str(error)
        }), 500


@routes.route("/ask", methods=["POST"])
def ask_question():

    global current_data
    global current_session_id

    try:
        restore_uploaded_files()

        if current_data is None:

            return jsonify({
                "error": "Please upload a CSV first"
            }), 400

        data = request.get_json(
            silent=True
        ) or {}

        question = data.get(
            "question",
            ""
        ).strip()

        if not question:

            return jsonify({
                "error": "Question is required"
            }), 400

        question_lower = question.lower()

        # Special profile questions
        if (
            "most missing" in question_lower
            or "highest missing" in question_lower
            or "maximum missing" in question_lower
        ):

            question_type = "profile"

        else:

            question_type = classify_question(
                question
            )

        generated_code = ""
        answer = ""
        result_value = None

        # ------------------------------------------------
        # PROFILE QUESTIONS
        # ------------------------------------------------

        if question_type == "profile":

            profile = get_profile(
                current_data,
                source_files=all_uploaded_files
            )

            # Most missing values
            if (
                "most missing" in question_lower
                or "highest missing" in question_lower
                or "maximum missing" in question_lower
            ):

                most_missing = max(
                    profile["column_details"],
                    key=lambda detail: detail["missing"]
                )
                column = most_missing["name"]
                count = most_missing["missing"]

                answer = (
                    f"The column with the most "
                    f"missing values is '{column}' "
                    f"with {count} missing values."
                )

            # Total missing
            elif "missing" in question_lower:

                answer = (
                    f"The dataset has "
                    f"{profile['total_missing']} "
                    f"missing values."
                )

            # Rows
            elif "row" in question_lower:

                answer = (
                    f"The dataset has "
                    f"{profile['rows']} rows."
                )

            # Columns
            elif "column" in question_lower:

                answer = (
                    f"The dataset has "
                    f"{profile['columns']} columns."
                )

            else:

                answer = (
                    "Dataset profile generated successfully."
                )

        # ------------------------------------------------
        # AI QUESTIONS
        # ------------------------------------------------

        else:

            generated_code = generate_code(
                question,
                list(current_data.columns),
                current_data.head(5).to_string(
                    index=False
                )
            )

            output = execute_code(
                generated_code,
                current_data
            )

            # ------------------------------------------------
            # REPAIR
            # ------------------------------------------------

            if not output["success"]:

                repair_prompt = f"""
The generated pandas code failed.

Question:
{question}

Code:
{generated_code}

Error:
{output['error']}

Return corrected pandas code only.

Rules:
1. Dataframe is available as df.
2. Store final answer in result.
3. Use only pandas and numpy.
4. Do not use files, network, OS or shell commands.
5. Do not use exec or eval.
"""

                from Backend.ai import (
                    client,
                    clean_code
                )

                response = client.chat.completions.create(

                    model="openai/gpt-oss-20b",

                    messages=[
                        {
                            "role": "user",
                            "content": repair_prompt
                        }
                    ],

                    temperature=0
                )

                generated_code = clean_code(
                    response.choices[0].message.content
                )

                output = execute_code(
                    generated_code,
                    current_data
                )

            # ------------------------------------------------
            # VERIFIED RESULT
            # ------------------------------------------------

            if output["success"]:

                result_value = output["result"]

                answer = explain_result(
                    question,
                    str(result_value)
                )

            # ------------------------------------------------
            # RAG FALLBACK
            # ------------------------------------------------

            else:

                try:

                    context = get_relevant_data(
                        "dataset_chunks",
                        question
                    )

                except Exception:

                    context = []

                if context:

                    answer = (
                        "Relevant dataset information:\n\n"
                        + "\n\n".join(
                            context[:3]
                        )
                    )

                else:

                    answer = (
                        "I could not calculate a "
                        "verified answer. Please try "
                        "rephrasing your question."
                    )

        # ------------------------------------------------
        # SAVE HISTORY
        # ------------------------------------------------

        if current_session_id:

            save_query(
                current_session_id,
                question,
                answer,
                generated_code
            )

        return jsonify({

            "question": question,

            "type": question_type,

            "answer": answer,

            "result": (
                str(result_value)
                if result_value is not None
                else None
            ),

            "code": generated_code

        })

    except Exception as error:

        print("\nASK ERROR:")
        print(error)

        return jsonify({
            "error": str(error)
        }), 500


@routes.route("/history-data")
def history_data():

    try:

        rows = get_history()

        history = []

        for row in rows:

            history.append({

                "question": row[0],

                "answer": row[1],

                "created_at": str(row[2])

            })

        return jsonify(history)

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500