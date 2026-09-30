import streamlit as st
import pandas as pd
import os
import ast

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")

if groq_key:
    groq = Groq(api_key=groq_key)


st.set_page_config(
    page_title="Conversational Data Analysis Assistant",
    layout="wide"
)


# -------------------------
# AST Safety Checker
# -------------------------

def check_code(code):

    try:
        tree = ast.parse(code)
    except:
        return False

    for node in ast.walk(tree):

        # Block imports
        if isinstance(node, ast.Import):
            return False

        if isinstance(node, ast.ImportFrom):
            return False

        # Check function calls
        if isinstance(node, ast.Call):

            if isinstance(node.func, ast.Name):

                if node.func.id in [
                    "exec",
                    "eval",
                    "open",
                    "__import__"
                ]:
                    return False

            if isinstance(node.func, ast.Attribute):

                if node.func.attr in [
                    "system",
                    "popen"
                ]:
                    return False

        # Block private attributes
        if isinstance(node, ast.Attribute):

            if node.attr.startswith("__"):
                return False

    return True


# -------------------------
# UI
# -------------------------

st.markdown("""
<style>

.stApp {
    background-color: #101722;
    color: #e8edf3;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
}

.title {
    font-size: 32px;
    font-weight: 600;
    color: #f5f7fa;
}

.subtitle {
    color: #8b98a9;
    margin-bottom: 30px;
}

.section {
    font-size: 19px;
    font-weight: 600;
    margin-top: 30px;
    margin-bottom: 12px;
}

</style>
""", unsafe_allow_html=True)


st.markdown(
    '<div class="title">Conversational Data Analysis Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Upload a dataset and ask questions about your data.'
    '</div>',
    unsafe_allow_html=True
)


# -------------------------
# Upload CSV
# -------------------------

st.markdown(
    '<div class="section">Upload your dataset</div>',
    unsafe_allow_html=True
)

file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"]
)


if file:

    try:

        # Find actual header row
        file.seek(0)

        text = file.read(5000).decode(
            "utf-8",
            errors="ignore"
        )

        file.seek(0)

        lines = text.splitlines()

        header = 0

        for i, line in enumerate(lines):

            if (
                "temperature" in line.lower()
                and "rh" in line.lower()
            ):
                header = i
                break


        # Read CSV
        file.seek(0)

        df = pd.read_csv(
            file,
            sep=None,
            engine="python",
            skiprows=header
        )


        # Clean column names
        df.columns = df.columns.str.strip()


        # Remove empty rows and columns
        df = df.dropna(
            axis=0,
            how="all"
        )

        df = df.dropna(
            axis=1,
            how="all"
        )


        # Clean object columns
        for col in df.columns:

            if df[col].dtype == "object":

                df[col] = (
                    df[col]
                    .astype(str)
                    .str.strip()
                )

                df[col] = df[col].replace(
                    ["nan", "NaN", ""],
                    None
                )


        # Convert numeric columns
        for col in df.columns:

            if col in ["day", "month", "Classes"]:
                continue

            numbers = pd.to_numeric(
                df[col],
                errors="coerce"
            )

            total = df[col].notna().sum()
            valid = numbers.notna().sum()

            if total > 0 and valid / total >= 0.8:
                df[col] = numbers


        st.success(
            "Dataset uploaded successfully."
        )


        # -------------------------
        # Dataset Overview
        # -------------------------

        st.markdown(
            '<div class="section">Dataset Overview</div>',
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Rows",
            len(df)
        )

        c2.metric(
            "Columns",
            len(df.columns)
        )

        c3.metric(
            "Missing Values",
            int(df.isna().sum().sum())
        )

        c4.metric(
            "Duplicates",
            int(df.duplicated().sum())
        )


        # -------------------------
        # Data Preview
        # -------------------------

        st.markdown(
            '<div class="section">Data Preview</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            df.head(10),
            use_container_width=True
        )


        # -------------------------
        # Column Information
        # -------------------------

        st.markdown(
            '<div class="section">Column Information</div>',
            unsafe_allow_html=True
        )

        info = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str),
            "Missing Values": df.isna().sum().values,
            "Unique Values": df.nunique().values
        })

        st.dataframe(
            info,
            use_container_width=True,
            hide_index=True
        )


        # -------------------------
        # Summary Statistics
        # -------------------------

        st.markdown(
            '<div class="section">Summary Statistics</div>',
            unsafe_allow_html=True
        )

        numbers = df.select_dtypes(
            include="number"
        )

        if not numbers.empty:

            st.dataframe(
                numbers.describe().round(2),
                use_container_width=True
            )


        # -------------------------
        # Ask Question
        # -------------------------

        st.markdown(
            '<div class="section">'
            'Ask a question about your data'
            '</div>',
            unsafe_allow_html=True
        )


        model = st.selectbox(
            "Select AI Model",
            [
                "GPT-OSS 20B",
                "GPT-OSS 120B"
            ]
        )


        question = st.chat_input(
            "Example: What is the highest FWI?"
        )


        if question:

            st.chat_message(
                "user"
            ).write(question)


            # Select model
            if model == "GPT-OSS 20B":

                selected_model = "openai/gpt-oss-20b"

            else:

                selected_model = "openai/gpt-oss-120b"


            # Dataset information
            columns = list(df.columns)

            dtypes = df.dtypes.astype(
                str
            ).to_dict()


            # -------------------------
            # Prompt
            # -------------------------

            prompt = f"""
You are a data analysis assistant.

The dataframe is called df.

Columns:
{columns}

Data types:
{dtypes}

User question:
{question}

Generate Python pandas code to answer the question.

Rules:
- df is already available.
- Use only df and pandas.
- Do not import anything.
- Do not read files.
- Do not write files.
- Do not use internet.
- Do not use os.
- Do not use subprocess.
- Do not use eval.
- Do not use exec.
- Store the final answer in a variable called result.
- Return only Python code.
- Do not explain anything.

Example:
result = df["FWI"].max()
"""


            try:

                # -------------------------
                # Groq
                # -------------------------

                if not groq_key:

                    st.error(
                        "Groq API key is missing."
                    )

                    st.stop()


                with st.spinner(
                    f"{model} is generating the answer..."
                ):

                    response = (
                        groq.chat.completions.create(

                            model=selected_model,

                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )
                    )


                code = (
                    response
                    .choices[0]
                    .message
                    .content
                )


                # -------------------------
                # Clean code
                # -------------------------

                code = code.strip()


                if "```python" in code:

                    code = code.replace(
                        "```python",
                        ""
                    )


                if "```" in code:

                    code = code.replace(
                        "```",
                        ""
                    )


                code = code.strip()


                # -------------------------
                # Show generated code
                # -------------------------

                st.chat_message(
                    "assistant"
                ).write(
                    "Generated Pandas code:"
                )

                st.code(
                    code,
                    language="python"
                )


                # -------------------------
                # AST Validation
                # -------------------------

                if not check_code(code):

                    st.error(
                        "Unsafe code detected. "
                        "The code was not executed."
                    )

                else:

                    st.success(
                        "Code passed safety check."
                    )


                    # -------------------------
                    # Execute code
                    # -------------------------

                    data = {
                        "df": df,
                        "pd": pd
                    }


                    exec(
                        code,
                        data
                    )


                    result = data.get(
                        "result"
                    )


                    # -------------------------
                    # Show result
                    # -------------------------

                    st.chat_message(
                        "assistant"
                    ).write(
                        "Result:"
                    )


                    if isinstance(
                        result,
                        pd.DataFrame
                    ):

                        st.dataframe(
                            result,
                            use_container_width=True
                        )


                    elif isinstance(
                        result,
                        pd.Series
                    ):

                        st.dataframe(
                            result
                        )


                    else:

                        st.write(
                            result
                        )


            except Exception as error:

                st.error(
                    "Error: " + str(error)
                )


    except Exception as error:

        st.error(
            "Could not read the file: " + str(error)
        )