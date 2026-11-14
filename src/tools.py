import logging
import sqlite3
from datetime import datetime

from chromadb.api.models.Collection import Collection
from pydantic import BaseModel

from db import get_connection
from embeddings import embed_texts
from index import retrieve, set_up_chroma

MAX_DISTANCE = 0.6


class SearchHit(BaseModel):
    item_id: str
    title: str | None
    url: str
    saved_day: int
    snippet: str | None
    distance: float


class SavedItemSummary(BaseModel):
    item_id: str
    title: str | None
    url: str
    saved_at: str


def search_saved(query: str, collection: Collection, connection: sqlite3.Connection, k: int = 5, embed=embed_texts,
                 domain=None, since=None, until=None) -> list[SearchHit]:
    n_chunks = k * 4
    data = retrieve(query=query, collection=collection, k=n_chunks, embed=embed, domain=domain, since=since,
                    until=until)
    if not data or data[0]["distance"] > MAX_DISTANCE:
        return []

    unique_items = {}
    for item in data:
        item_id = item["item_id"]
        if item_id not in unique_items:
            unique_items[item_id] = {
                "distance": item["distance"],
                "saved_day": item["saved_day"],
                "text": item["text"]
            }

    top = list(unique_items.items())[:k]
    ids = [item_id for item_id, _ in top]
    placeholders = ",".join("?" * len(ids))  # "?,?,?"
    rows = connection.execute(f"SELECT * FROM saved_items WHERE id IN ({placeholders})", ids).fetchall()

    results = []
    titles = {r["id"]: r for r in rows}
    for item_id, hit in top:  # dict ensure the insertion order
        row = titles.get(item_id)
        if not row:
            logging.warning(f"Missing saved_item {item_id}")
            continue
        results.append(SearchHit(title=row["title"], item_id=item_id, url=row["url"],
                                 saved_day=hit["saved_day"], snippet=hit["text"][:200],
                                 distance=hit["distance"]))
    return results


def list_saves(connection: sqlite3.Connection, limit: int = 10,
               domain: str | None = None, since: datetime | None = None) -> list[SavedItemSummary]:
    query = "SELECT * FROM saved_items"
    conditions = []
    params = []
    if domain is not None:
        conditions.append("domain = ?")
        params.append(domain)
    if since is not None:
        conditions.append("saved_at >= ?")
        params.append(since.isoformat())

    if len(conditions) > 0:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY saved_at DESC"
    query += " LIMIT ?"
    params.append(limit)
    saved_items = connection.execute(query, params).fetchall()

    results = []
    for item in saved_items:
        results.append(SavedItemSummary(item_id=item["id"], title=item["title"],
                                        url=item["url"], saved_at=item["saved_at"]))
    return results


if __name__ == '__main__':
    clt = set_up_chroma()
    conn = get_connection()
    # llm_answer = search_saved("python", clt, conn)
    # print(llm_answer)

    items = list_saves(conn, domain="docs.python.org")
    print(items)
