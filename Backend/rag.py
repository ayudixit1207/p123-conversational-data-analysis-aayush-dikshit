from Backend.embedding import create_embedding
from Backend.qdrant import search_vectors


def get_relevant_data(
    collection_name,
    question,
    limit=5
):

    vector = create_embedding(
        question
    )

    results = search_vectors(
        collection_name,
        vector,
        limit
    )

    context = []

    for item in results:

        if item.payload:

            context.append(
                item.payload.get("text", "")
            )

    return context