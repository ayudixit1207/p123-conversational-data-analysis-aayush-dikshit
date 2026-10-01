import ast


allowed_imports = {
    "pandas",
    "numpy"
}


blocked_functions = {
    "open",
    "exec",
    "eval",
    "input",
    "compile",
    "__import__"
}


def check_code(code):

    try:

        tree = ast.parse(code)

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for item in node.names:

                    if item.name not in allowed_imports:
                        return False

            if isinstance(node, ast.ImportFrom):

                if node.module not in allowed_imports:
                    return False

            if isinstance(node, ast.Call):

                if isinstance(
                    node.func,
                    ast.Name
                ):

                    if node.func.id in blocked_functions:
                        return False

            if isinstance(node, ast.Attribute):

                if node.attr.startswith("__"):
                    return False

        return True

    except Exception:

        return False