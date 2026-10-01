from flask import Blueprint, jsonify, request, render_template
import pandas as pd
import numpy as np
import os
from pathlib import Path
import uuid

from Backend.ingestion import save_file, read_csv
from Backend.processing import get_profile
from Backend.chunking import create_chunks, create_text
from Backend.embedding import create_embeddings
from Backend.qdrant import (
    store_vectors,
    delete_collection
)
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

    known_paths = {
        os.path.normcase(os.path.abspath(file_info["path"]))
        for file_info in all_uploaded_files
    }
    restored_frames = []

    for path in sorted(Path("Uploads").glob("*.csv")):
        normalized_path = os.path.normcase(os.path.abspath(path))
        if normalized_path in known_paths:
            continue

        try:
            dataframe = read_csv(str(path))
        except Exception as error:
            print(f"Could not load uploaded file {path.name}: {error}")
            continue

        stored_name = path.name
        prefix, separator, original_name = stored_name.partition("_")
        if (
            separator
            and len(prefix) == 32
            and all(character in "0123456789abcdef" for character in prefix.lower())
        ):
            stored_name = original_name

        all_uploaded_files.append({
            "id": path.name,
            "name": stored_name,
            "path": str(path),
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
            "schema": list(dataframe.columns)
        })
        restored_frames.append(dataframe)

    if restored_frames:
        frames = ([current_data] if current_data is not None else []) + restored_frames
        current_data = pd.concat(frames, ignore_index=True)


# ==================================================
# PAGES
# ==================================================

@routes.route("/")
def home():

    return render_template(
        "index.html"
    )


@routes.route("/files")
def files_page():

    restore_uploaded_files()

    return render_template(
        "files.html"
    )


@routes.route("/ask-page")
def ask_page():

    return render_template(
        "ask.html"
    )


@routes.route("/history")
def history_page():

    return render_template(
        "history.html"
    )


# ==================================================
# CHART DATA
# ==================================================

def make_chart_data(data, question):

    question = question.lower()

    numeric_columns = (
        data
        .select_dtypes(
            include="number"
        )
        .columns
        .tolist()
    )

    categorical_columns = (
        data
        .select_dtypes(
            include="object"
        )
        .columns
        .tolist()
    )

    chart = {
        "type": None,
        "title": "",
        "labels": [],
        "values": [],
        "points": [],
        "matrix": []
    }


    # =================================================
    # PIE
    # =================================================

    if "pie" in question:

        if len(categorical_columns) > 0:

            column = categorical_columns[0]

            counts = (
                data[column]
                .dropna()
                .value_counts()
                .head(8)
            )

            chart["type"] = "pie"

            chart["title"] = (
                f"Distribution of {column}"
            )

            chart["labels"] = [
                str(value)
                for value in counts.index
            ]

            chart["values"] = [
                int(value)
                for value in counts.values
            ]


    # =================================================
    # HEATMAP
    # =================================================

    elif "heatmap" in question:

        heatmap_columns = [
            column
            for column in numeric_columns
            if column.lower() not in [
                "id",
                "employee_id",
                "student_id",
                "user_id"
            ]
        ]

        if len(heatmap_columns) >= 2:

            correlation = (
                data[heatmap_columns]
                .corr()
                .fillna(0)
                .round(2)
            )

            chart["type"] = "heatmap"

            chart["title"] = (
                "Correlation Heatmap"
            )

            chart["labels"] = [
                str(column)
                for column in heatmap_columns
            ]

            chart["matrix"] = [
                [
                    float(value)
                    for value in row
                ]
                for row in correlation.values
            ]


    # =================================================
    # HISTOGRAM
    # =================================================

    elif "histogram" in question:

        if len(numeric_columns) > 0:

            column = numeric_columns[0]

            values = (
                pd.to_numeric(
                    data[column],
                    errors="coerce"
                )
                .dropna()
            )

            if len(values) > 0:

                counts, bins = np.histogram(
                    values,
                    bins=10
                )

                chart["type"] = "histogram"

                chart["title"] = (
                    f"Distribution of {column}"
                )

                chart["labels"] = [
                    round(float(value), 2)
                    for value in bins[:-1]
                ]

                chart["values"] = [
                    int(value)
                    for value in counts
                ]


    # =================================================
    # SCATTER
    # =================================================

    elif "scatter" in question:

        if len(numeric_columns) >= 2:

            x_column = numeric_columns[0]

            y_column = numeric_columns[1]

            clean_data = (
                data[
                    [x_column, y_column]
                ]
                .apply(
                    pd.to_numeric,
                    errors="coerce"
                )
                .dropna()
                .head(500)
            )

            chart["type"] = "scatter"

            chart["title"] = (
                f"{x_column} vs {y_column}"
            )

            chart["points"] = [
                {
                    "x": float(row[x_column]),
                    "y": float(row[y_column])
                }
                for _, row
                in clean_data.iterrows()
            ]


    # =================================================
    # LINE
    # =================================================

    elif "line" in question:

        if len(numeric_columns) > 0:

            column = numeric_columns[0]

            values = (
                pd.to_numeric(
                    data[column],
                    errors="coerce"
                )
                .dropna()
                .head(200)
            )

            chart["type"] = "line"

            chart["title"] = (
                f"{column} Trend"
            )

            chart["labels"] = [
                str(i + 1)
                for i in range(len(values))
            ]

            chart["values"] = [
                float(value)
                for value in values
            ]


    # =================================================
    # BAR
    # =================================================

    elif "bar" in question:

        if len(categorical_columns) > 0:

            column = categorical_columns[0]

            counts = (
                data[column]
                .dropna()
                .value_counts()
                .head(10)
            )

            chart["type"] = "bar"

            chart["title"] = (
                f"{column} Distribution"
            )

            chart["labels"] = [
                str(value)
                for value in counts.index
            ]

            chart["values"] = [
                int(value)
                for value in counts.values
            ]

        elif len(numeric_columns) > 0:

            column = numeric_columns[0]

            values = (
                pd.to_numeric(
                    data[column],
                    errors="coerce"
                )
                .dropna()
                .head(10)
            )

            chart["type"] = "bar"

            chart["title"] = (
                f"{column} Values"
            )

            chart["labels"] = [
                str(i + 1)
                for i in range(len(values))
            ]

            chart["values"] = [
                float(value)
                for value in values
            ]


    return chart


# ==================================================
# UPLOAD
# ==================================================

@routes.route(
    "/upload",
    methods=["POST"]
)
def upload_file():

    global current_data
    global current_dataset_id
    global current_session_id
    global all_uploaded_files

    try:

        restore_uploaded_files()

        if "files" in request.files:

            files = request.files.getlist(
                "files"
            )

        elif "file" in request.files:

            files = [
                request.files["file"]
            ]

        else:

            return jsonify({
                "error":
                    "No file uploaded"
            }), 400


        new_data = []
        new_files = []


        for file in files:

            if not file.filename:
                continue

            if not file.filename.lower().endswith(
                ".csv"
            ):
                continue


            file_path = save_file(
                file
            )

            data = read_csv(
                file_path
            )


            new_data.append(
                data
            )


            new_files.append({

                "id":
                    os.path.basename(file_path),

                "name":
                    file.filename,

                "path":
                    file_path,

                "rows":
                    len(data),

                "columns":
                    len(data.columns),

                "schema":
                    list(data.columns)

            })


        if not new_data:

            return jsonify({
                "error":
                    "No valid CSV files found"
            }), 400


        # ------------------------------------------
        # COMBINE DATA
        # ------------------------------------------

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


        all_uploaded_files.extend(
            new_files
        )


        # ------------------------------------------
        # DATABASE
        # ------------------------------------------

        for file_info in new_files:

            dataset_id = save_dataset(

                file_info["name"],

                file_info["path"],

                file_info["rows"],

                file_info["columns"]

            )


            if current_dataset_id is None:

                current_dataset_id = (
                    dataset_id
                )


        if current_session_id is None:

            current_session_id = (
                create_session(
                    current_dataset_id
                )
            )


        # ------------------------------------------
        # PROFILE
        # ------------------------------------------

        profile = get_profile(
            current_data,
            source_files=all_uploaded_files
        )


        profile["total_files"] = (
            len(all_uploaded_files)
        )


        profile["files"] = (
            [public_file_info(file) for file in all_uploaded_files]
        )


        # ------------------------------------------
        # CHUNKS
        # ------------------------------------------

        texts = []

        vector_file_names = []


        for index, data in enumerate(
            new_data
        ):

            chunks = create_chunks(
                data
            )


            for chunk in chunks:

                texts.append(
                    create_text(
                        chunk
                    )
                )


                vector_file_names.append(
                    new_files[index]["name"]
                )


        # ------------------------------------------
        # EMBEDDINGS + QDRANT
        # ------------------------------------------

        if len(texts) > 0:

            vectors = create_embeddings(
                texts
            )


            store_vectors(

                "dataset_chunks",

                vectors,

                texts,

                vector_file_names

            )


        return jsonify({

            "message":
                "Files uploaded successfully",

            "files":
                [public_file_info(file) for file in all_uploaded_files],

            "total_files":
                len(all_uploaded_files),

            "profile":
                profile

        })


    except Exception as error:

        print(
            "\nUPLOAD ERROR:"
        )

        print(error)


        return jsonify({
            "error": str(error)
        }), 500


# ==================================================
# FILE LIST
# ==================================================

@routes.route("/files-data")
def files_data():

    restore_uploaded_files()

    return jsonify({

        "files":
            [public_file_info(file) for file in all_uploaded_files]

    })


@routes.route("/profile")
def dataset_profile():

    restore_uploaded_files()

    if current_data is None:
        profile = {
            "rows": 0,
            "columns": 0,
            "total_missing": 0,
            "duplicate_rows": 0,
            "column_details": [],
            "numeric_summary": [],
            "preview": [],
        }
    else:
        profile = get_profile(
            current_data,
            source_files=all_uploaded_files,
        )

    profile["total_files"] = len(all_uploaded_files)
    profile["files"] = [
        public_file_info(file)
        for file in all_uploaded_files
    ]

    return jsonify({"profile": profile})


# ==================================================
# DELETE FILE
# ==================================================

@routes.route(
    "/delete-file",
    methods=["POST"]
)
def delete_file():

    global current_data
    global current_dataset_id
    global current_session_id
    global all_uploaded_files

    try:

        restore_uploaded_files()

        data = request.get_json(
            silent=True
        ) or {}


        file_id = data.get("file_id")


        if not file_id:

            return jsonify({
                "error":
                    "File ID is required"
            }), 400


        # ------------------------------------------
        # FIND FILE
        # ------------------------------------------

        selected_file = None


        selected_file = next(
            (
                file_info
                for file_info in all_uploaded_files
                if file_info["id"] == file_id
            ),
            None
        )


        if selected_file is None:

            return jsonify({
                "error":
                    "File not found"
            }), 404


        # ------------------------------------------
        # DELETE PHYSICAL FILE
        # ------------------------------------------

        file_path = selected_file.get(
            "path"
        )


        if (
            file_path
            and os.path.exists(file_path)
        ):

            os.remove(
                file_path
            )


        # ------------------------------------------
        # REMOVE FROM ACTIVE LIST
        # ------------------------------------------

        all_uploaded_files = [
            file_info
            for file_info
            in all_uploaded_files
            if file_info["id"] != file_id
        ]


        # ------------------------------------------
        # REBUILD DATA
        # ------------------------------------------

        dataframes = []


        for file_info in all_uploaded_files:

            path = file_info.get(
                "path"
            )


            if (
                path
                and os.path.exists(path)
            ):

                dataframe = read_csv(
                    path
                )

                dataframes.append(
                    dataframe
                )


        if dataframes:

            current_data = pd.concat(
                dataframes,
                ignore_index=True
            )

        else:

            current_data = None

        current_dataset_id = None
        current_session_id = None


        # ------------------------------------------
        # REBUILD QDRANT
        # ------------------------------------------

        try:

            delete_collection(
                "dataset_chunks"
            )

        except Exception as error:

            print(
                "Qdrant delete error:",
                error
            )


        if dataframes:

            texts = []

            vector_file_names = []


            for index, dataframe in enumerate(
                dataframes
            ):

                chunks = create_chunks(
                    dataframe
                )


                current_file_name = (
                    all_uploaded_files[index]
                    ["name"]
                )


                for chunk in chunks:

                    texts.append(
                        create_text(
                            chunk
                        )
                    )


                    vector_file_names.append(
                        current_file_name
                    )


            if texts:

                vectors = create_embeddings(
                    texts
                )


                store_vectors(

                    "dataset_chunks",

                    vectors,

                    texts,

                    vector_file_names

                )


        # ------------------------------------------
        # PROFILE
        # ------------------------------------------

        if current_data is not None:

            profile = get_profile(
                current_data,
                source_files=all_uploaded_files,
            )

        else:
            profile = {
                "rows": 0,
                "columns": 0,
                "total_missing": 0,
                "duplicate_rows": 0,
                "column_details": [],
                "numeric_summary": [],
                "categorical_summary": [],
                "preview": [],
                "preview_groups": [],
            }


        profile["total_files"] = (
            len(all_uploaded_files)
        )


        profile["files"] = (
            [public_file_info(file) for file in all_uploaded_files]
        )


        return jsonify({

            "message":
                f"{selected_file['name']} deleted successfully.",

            "files":
                [public_file_info(file) for file in all_uploaded_files],

            "total_files":
                len(all_uploaded_files),

            "profile":
                profile

        })


    except Exception as error:

        print(
            "\nDELETE FILE ERROR:"
        )

        print(error)


        return jsonify({
            "error": str(error)
        }), 500


# ==================================================
# ASK
# ==================================================

@routes.route(
    "/ask",
    methods=["POST"]
)
def ask_question():

    global current_data
    global current_session_id

    try:

        restore_uploaded_files()

        if current_data is None:

            return jsonify({
                "error":
                    "Please upload a CSV first"
            }), 400


        request_data = request.get_json(
            silent=True
        ) or {}


        question = request_data.get(
            "question",
            ""
        ).strip()


        if not question:

            return jsonify({
                "error":
                    "Question is required"
            }), 400


        question_lower = (
            question.lower()
        )


        # ------------------------------------------
        # CHART DETECTION
        # ------------------------------------------

        chart_words = [

            "chart",

            "graph",

            "plot",

            "histogram",

            "bar",

            "line",

            "pie",

            "scatter",

            "heatmap"

        ]


        is_chart_question = any(

            word in question_lower

            for word in chart_words

        )


        # ------------------------------------------
        # QUESTION TYPE
        # ------------------------------------------

        if (

            "most missing"
            in question_lower

            or

            "highest missing"
            in question_lower

            or

            "maximum missing"
            in question_lower

        ):

            question_type = "profile"


        elif is_chart_question:

            question_type = "chart"


        else:

            question_type = (
                classify_question(
                    question
                )
            )


        generated_code = ""

        answer = ""

        result_value = None


        # ==========================================
        # CHART
        # ==========================================

        if question_type == "chart":

            chart = make_chart_data(

                current_data,

                question

            )


            if chart["type"] is None:

                answer = (
                    "I could not create the "
                    "requested chart from the "
                    "available data."
                )

            else:

                answer = (
                    "Chart generated from "
                    "the uploaded data."
                )


            if current_session_id:

                save_query(

                    current_session_id,

                    question,

                    answer,

                    ""

                )


            return jsonify({

                "question":
                    question,

                "type":
                    "chart",

                "answer":
                    answer,

                "result":
                    None,

                "code":
                    "",

                "chart":
                    chart

            })


        # ==========================================
        # PROFILE QUESTIONS
        # ==========================================

        if question_type == "profile":

            profile = get_profile(
                current_data,
                source_files=all_uploaded_files
            )


            if (

                "most missing"
                in question_lower

                or

                "highest missing"
                in question_lower

                or

                "maximum missing"
                in question_lower

            ):

                most_missing = max(
                    profile["column_details"],
                    key=lambda detail: detail["missing"]
                )
                column = most_missing["name"]
                count = most_missing["missing"]


                answer = (

                    f"The column with the "

                    f"most missing values "

                    f"is '{column}' with "

                    f"{count} missing values."

                )


            elif "missing" in question_lower:

                answer = (

                    f"The dataset has "

                    f"{profile['total_missing']} "

                    f"missing values."

                )


            elif "row" in question_lower:

                answer = (

                    f"The dataset has "

                    f"{profile['rows']} rows."

                )


            elif "column" in question_lower:

                answer = (

                    f"The dataset has "

                    f"{profile['columns']} columns."

                )


            else:

                answer = (
                    "Dataset profile generated "
                    "successfully."
                )


        # ==========================================
        # AI QUESTIONS
        # ==========================================

        else:

            generated_code = generate_code(

                question,

                list(
                    current_data.columns
                ),

                current_data.head(
                    5
                ).to_string(
                    index=False
                )

            )


            output = execute_code(

                generated_code,

                current_data

            )


            # --------------------------------------
            # REPAIR
            # --------------------------------------

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


                response = (

                    client
                    .chat
                    .completions
                    .create(

                        model=
                            "openai/gpt-oss-20b",

                        messages=[

                            {

                                "role":
                                    "user",

                                "content":
                                    repair_prompt

                            }

                        ],

                        temperature=0

                    )

                )


                generated_code = clean_code(

                    response
                    .choices[0]
                    .message
                    .content

                )


                output = execute_code(

                    generated_code,

                    current_data

                )


            # --------------------------------------
            # VERIFIED RESULT
            # --------------------------------------

            if output["success"]:

                result_value = (
                    output["result"]
                )


                answer = explain_result(

                    question,

                    str(result_value)

                )


            # --------------------------------------
            # RAG FALLBACK
            # --------------------------------------

            else:

                try:

                    context = (

                        get_relevant_data(

                            "dataset_chunks",

                            question

                        )

                    )

                except Exception:

                    context = []


                if context:

                    answer = (

                        "Relevant dataset "
                        "information:\n\n"

                        +

                        "\n\n".join(
                            context[:3]
                        )

                    )

                else:

                    answer = (

                        "I could not calculate "
                        "a verified answer. "
                        "Please try rephrasing "
                        "your question."

                    )


        # ==========================================
        # SAVE HISTORY
        # ==========================================

        if current_session_id:

            save_query(

                current_session_id,

                question,

                answer,

                generated_code

            )


        return jsonify({

            "question":
                question,

            "type":
                question_type,

            "answer":
                answer,

            "result":

                (

                    str(result_value)

                    if result_value is not None

                    else None

                ),

            "code":
                generated_code

        })


    except Exception as error:

        print(
            "\nASK ERROR:"
        )

        print(error)


        return jsonify({
            "error": str(error)
        }), 500


# ==================================================
# HISTORY
# ==================================================

@routes.route("/history-data")
def history_data():

    try:

        rows = get_history()

        history = []


        for row in rows:

            history.append({

                "question":
                    row[0],

                "answer":
                    row[1],

                "created_at":
                    str(row[2])

            })


        return jsonify(
            history
        )


    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500