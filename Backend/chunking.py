def create_chunks(data, chunk_size=20):

    chunks = []

    for start in range(
        0,
        len(data),
        chunk_size
    ):

        chunk = data.iloc[
            start:start + chunk_size
        ]

        chunks.append(chunk)

    return chunks


def create_text(chunk):

    return chunk.to_string(
        index=False
    )