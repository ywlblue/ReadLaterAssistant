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


if __name__ == '__main__':
    conn = connect()
    clt = set_up_chroma()
    count = build_index(clt, conn)
    print(f"Result: {count}")
    conn.close()
