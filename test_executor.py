import pandas as pd

from Backend.executor import execute_code


data = pd.DataFrame({
    "name": ["A", "B", "C"],
    "salary": [20000, 30000, 40000]
})


code = """
result = df["salary"].mean()
"""


output = execute_code(
    code,
    data
)


print(output)