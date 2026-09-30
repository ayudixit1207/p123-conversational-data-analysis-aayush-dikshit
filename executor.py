import sys
import pickle
import pandas as pd


def run_code(code, df):

    data = {
        "df": df,
        "pd": pd
    }

    exec(code, data)

    return data.get("result")


if __name__ == "__main__":

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:

        with open(input_file, "rb") as file:
            df = pickle.load(file)

        code = open(
            input_file + ".code",
            "r",
            encoding="utf-8"
        ).read()

        result = run_code(
            code,
            df
        )

        with open(output_file, "wb") as file:
            pickle.dump(
                {
                    "success": True,
                    "result": result
                },
                file
            )

    except Exception as error:

        with open(output_file, "wb") as file:
            pickle.dump(
                {
                    "success": False,
                    "error": str(error)
                },
                file
            )