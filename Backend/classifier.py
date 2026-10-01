def classify_question(question):

    question = question.lower()

    if any(word in question for word in [
        "row",
        "rows",
        "column",
        "columns",
        "missing"
    ]):
        return "profile"

    if any(word in question for word in [
        "average",
        "mean",
        "sum",
        "total",
        "maximum",
        "minimum",
        "max",
        "min",
        "count"
    ]):
        return "calculation"

    if any(word in question for word in [
        "chart",
        "graph",
        "plot",
        "distribution"
    ]):
        return "chart"

    return "general"