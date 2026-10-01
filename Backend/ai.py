import os
import re

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


client = Groq(
    api_key=os.getenv(
        "GROQ_API_KEY"
    )
)


def clean_code(code):

    code = code.strip()

    code = re.sub(
        r"```python",
        "",
        code,
        flags=re.IGNORECASE
    )

    code = code.replace(
        "```",
        ""
    )

    return code.strip()


def generate_code(
    question,
    columns,
    sample
):

    prompt = f"""
You are a Python pandas data analyst.

Dataset columns:
{columns}

Dataset sample:
{sample}

User question:
{question}

Write only Python pandas code.

Rules:
1. The dataframe is already available as df.
2. Store the final answer in a variable named result.
3. Use only pandas and numpy.
4. Do not import anything.
5. Do not use files, network, OS, subprocess or shell commands.
6. Do not use exec or eval.
7. Return only code.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    code = response.choices[0].message.content

    return clean_code(code)


def explain_result(
    question,
    result
):

    prompt = f"""
You are a data analysis assistant.

Question:
{question}

Verified result:
{result}

Explain the result in simple language.

Do not invent any additional numbers.
Use only the verified result.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content