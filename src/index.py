import sqlite3
from datetime import datetime
from math import ceil
from typing import Iterator

import chromadb
from chromadb.api.models.Collection import Collection

from chunks import Strategy
from embeddings import embed_texts, EMBEDDING_MODEL
from storage import connect

COLLECTION_NAME = f"chunks_{Strategy().strategy_info}_{EMBEDDING_MODEL}"


def set_up_chroma():
    client = chromadb.PersistentClient(path="data/chroma")
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_chunks(conn: sqlite3.Connection, count: int = 100) -> Iterator[list[dict]]:
    cursor = conn.execute("""
                    SELECT
                    c.id AS chunk_id,
                    c.content_text AS chunk_content,
                    c.item_id AS item_id,
                    s.url AS url,
                    s.domain AS domain,
                    CAST(strftime('%Y%m%d', s.saved_at) AS INTEGER) AS saved_day,
                    s.saved_at_origin AS saved_at_origin,
                    c.chunk_index AS chunk_index
                FROM saved_items s
                INNER JOIN chunks c ON s.id = c.item_id
            """)

    while rows := cursor.fetchmany(count):
        yield [dict(row) for row in rows]


def build_index(collection: Collection, conn: sqlite3.Connection, embed=embed_texts):
    for chunks in load_chunks(conn):
        chunk_ids = []
        documents = []
        metadata_lists = []

        for chunk in chunks:
            chunk_ids.append(str(chunk["chunk_id"]))
            documents.append(chunk["chunk_content"])

            metadata = {
                "item_id": str(chunk["item_id"]),
                "url": chunk["url"],
                "domain": chunk["domain"],
                "saved_day": chunk["saved_day"],
                "saved_at_origin": chunk["saved_at_origin"],
                "chunk_index": chunk["chunk_index"],
            }

            metadata_lists.append({
                key: value
                for key, value in metadata.items()
                if value is not None
            })

        collection.upsert(
            ids=chunk_ids,
            documents=documents,
            embeddings=embed(documents),
            metadatas=metadata_lists,
        )
        print(f"upserted {collection.count()}")

    return collection.count()


def build_where(
    domain: str | None = None,
    since: int | None = None,
    until: int | None = None,
) -> dict | None:
    conditions = []

    if domain:
        conditions.append({"domain": domain})

    if since is not None:
        conditions.append({"saved_day": {"$gte": since}})

    if until is not None:
        conditions.append({"saved_day": {"$lte": until}})

    if not conditions:
        return None

    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}


def retrieve(query: str, collection: Collection, k: int, domain=None, since=None, until=None):
    query_vector = embed_texts([query])[0]
    result = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where=build_where(domain, since, until),
    )
    # chunk_id、item_id、url、domain、saved_day、distance、text
    data = []
    for chunk_id, document, metadata, distance in zip(result["ids"][0], result["documents"][0],
                                                      result["metadatas"][0], result["distances"][0]):
        data.append({"chunk_id": chunk_id,
                     "item_id": metadata["item_id"],
                     "url": metadata["url"],
                     "domain": metadata["domain"],
                     "text": document,
                     "saved_day": metadata["saved_day"],
                     "distance": distance})

    return data


if __name__ == '__main__':
    conn = connect()
    clt = set_up_chroma()
    count = build_index(clt, conn)
    print(f"Result: {count}")
    conn.close()
    print("============TEST DOMAIN===============")
    data = retrieve("dynamic programming", clt, 5, domain="www.geeksforgeeks.org")
    print(data)
    print("\n\n\n")
    print("============TEST DATE===============")
    data = retrieve("dynamic programming", clt, 5, since=20261012, until=20261015)
    print(data)