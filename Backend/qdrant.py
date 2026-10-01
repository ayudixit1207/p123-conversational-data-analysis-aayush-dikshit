from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid


# Qdrant memory me chalega
# Isse local qdrant_storage lock problem nahi hogi
client = QdrantClient(":memory:")

VECTOR_SIZE = 384


def create_collection(collection_name):

    collections = client.get_collections()

    names = [
        collection.name
        for collection in collections.collections
    ]

    if collection_name not in names:

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )


def store_vectors(
    collection_name,
    vectors,
    texts,
    file_names
):

    create_collection(collection_name)

    points = []

    for i, vector in enumerate(vectors):

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": texts[i],
                    "file_name": file_names[i]
                }
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=points
    )


def search_vectors(
    collection_name,
    vector,
    limit=5
):

    result = client.query_points(
        collection_name=collection_name,
        query=vector,
        limit=limit,
        with_payload=True
    )

    return result.points


def delete_collection(collection_name):

    collections = client.get_collections()

    names = [
        collection.name
        for collection in collections.collections
    ]

    if collection_name in names:

        client.delete_collection(
            collection_name=collection_name
        )