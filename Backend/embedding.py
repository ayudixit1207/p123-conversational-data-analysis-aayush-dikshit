from sentence_transformers import SentenceTransformer


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def create_embeddings(texts):

    vectors = model.encode(
        texts,
        convert_to_numpy=True
    )

    return vectors.tolist()


def create_embedding(text):

    vector = model.encode(
        text,
        convert_to_numpy=True
    )

    return vector.tolist()