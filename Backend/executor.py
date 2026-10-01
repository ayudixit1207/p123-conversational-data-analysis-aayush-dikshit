import multiprocessing
import pandas as pd
import numpy as np

from Backend.saftey import check_code


# Maximum time allowed for generated code
EXECUTION_TIMEOUT = 5


def _execute_worker(code, data, result_queue):
    """
    Runs generated pandas code in a separate process.
    The separate process allows us to terminate execution
    if the generated code takes too long.
    """

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

        result = local_data.get("result")

        if result is None:
            result_queue.put({
                "success": False,
                "error": "No verified result was generated"
            })
            return

        result_queue.put({
            "success": True,
            "result": result
        })

    except Exception as error:
        result_queue.put({
            "success": False,
            "error": str(error)
        })


def execute_code(code, data):

    # ------------------------------------------
    # SAFETY CHECK
    # ------------------------------------------

    if not check_code(code):
        return {
            "success": False,
            "error": "Unsafe code blocked"
        }

    # ------------------------------------------
    # CREATE SEPARATE PROCESS
    # ------------------------------------------

    result_queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        target=_execute_worker,
        args=(
            code,
            data,
            result_queue
        )
    )

    process.daemon = True
    process.start()

    # ------------------------------------------
    # WAIT WITH TIMEOUT
    # ------------------------------------------

    process.join(
        EXECUTION_TIMEOUT
    )

    # ------------------------------------------
    # TIMEOUT
    # ------------------------------------------

    if process.is_alive():

        process.terminate()
        process.join()

        return {
            "success": False,
            "error": (
                f"Code execution timed out "
                f"after {EXECUTION_TIMEOUT} seconds"
            )
        }

    # ------------------------------------------
    # GET RESULT
    # ------------------------------------------

    if result_queue.empty():

        return {
            "success": False,
            "error": "Execution failed without a result"
        }

    output = result_queue.get()

    # ------------------------------------------
    # CLEANUP
    # ------------------------------------------

    result_queue.close()
    result_queue.join_thread()

    return output
