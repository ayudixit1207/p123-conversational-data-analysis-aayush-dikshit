def create_primary_chunks(data, chunk_size=50):
    primary_chunks = []

    for start in range(0, len(data), chunk_size):
        chunk = data.iloc[start:start + chunk_size].copy()
        primary_chunks.append(chunk)

    return primary_chunks


def create_secondary_chunks(primary_chunk, chunk_size=10):
    secondary_chunks = []

    for start in range(0, len(primary_chunk), chunk_size):
        chunk = primary_chunk.iloc[start:start + chunk_size].copy()
        secondary_chunks.append(chunk)

    return secondary_chunks


def create_text(chunk):
    return chunk.to_string(index=False)


def create_all_chunks(data):
    primary_chunks = create_primary_chunks(data)

    secondary_chunks = []

    for primary_chunk in primary_chunks:
        parts = create_secondary_chunks(primary_chunk)

        for part in parts:
            secondary_chunks.append(part)

    texts = []

    for chunk in secondary_chunks:
        texts.append(create_text(chunk))

    return texts