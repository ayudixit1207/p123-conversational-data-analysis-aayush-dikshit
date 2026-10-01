import pandas as pd

from Backend.executor import execute_code


def test_none_result_is_an_execution_failure():
    output = execute_code("result = None", pd.DataFrame())

    assert output["success"] is False
    assert output["result_is_none"] is True
