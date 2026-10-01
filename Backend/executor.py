import pandas as pd
import numpy as np

from Backend.saftey import check_code


def execute_code(code, data):

    if not check_code(code):

        return {
            "success": False,
            "error": "Unsafe code blocked"
        }

    try:

        local_data = {
            "df": data,
            "pd": pd,
            "np": np
        }

        exec(
            code,
            {
                "__builtins__": {}
            },
            local_data
        )

        result = local_data.get(
            "result"
        )

        return {
            "success": True,
            "result": result
        }

    except Exception as error:

        return {
            "success": False,
            "error": str(error)
        }