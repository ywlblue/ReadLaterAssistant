import re
import sqlite3

from chunks import Strategy
from db import get_connection


def create_fts(conn: sqlite3.Connection):
    conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id UNINDEXED,
                item_id  UNINDEXED,
                content_text,
                tokenize = 'porter unicode61'
            );
    """)
    conn.commit()


def insert_data(conn: sqlite3.Connection, strategy_info: str):
    conn.execute("DELETE FROM chunks_fts;")
    conn.execute("""
        INSERT INTO chunks_fts (chunk_id, item_id, content_text)
        SELECT id, item_id, content_text FROM chunks WHERE strategy = ?;
        """, (strategy_info,))
    conn.commit()


def build_fts(conn: sqlite3.Connection, strategy_info: str):
    create_fts(conn)
    insert_data(conn, strategy_info)


def fts_chunk_count() -> int:
    conn = get_connection()
    try:
        return conn.execute("SELECT count(*) FROM chunks_fts").fetchone()[0]
    finally:
        conn.close()


def lexical_search(query: str, k: int, domain=None, since=None, until=None) -> list[dict]:
    keywords = re.findall(r"\w+", query)
    if not keywords:
        return []

    conn = get_connection()

    search_str = " OR ".join(f'"{keyword}"' for keyword in keywords)
    search_query = """
        SELECT f.chunk_id AS chunk_id, f.item_id AS item_id, f.content_text AS text, 
        s.url AS url, s.domain AS domain, 
        CAST(strftime('%Y%m%d', s.saved_at) AS INTEGER) AS saved_day, 
        bm25(chunks_fts) AS score
        FROM chunks_fts f
        JOIN saved_items s ON s.id = f.item_id
    """
    conditions = ["chunks_fts MATCH ?"]
    params = [search_str]

    if domain is not None:
        conditions.append("s.domain = ?")
        params.append(domain)

    if since is not None:
        conditions.append("saved_day >= ?")
        params.append(since)

    if until is not None:
        conditions.append("saved_day <= ?")
        params.append(until)

    search_query += " WHERE " + " AND ".join(conditions)
    search_query += " ORDER BY score"
    search_query += " LIMIT " + str(k)

    rows = conn.execute(search_query, params).fetchall()

    conn.close()

    data = []
    for row in rows:
        data.append({"chunk_id": row["chunk_id"],
                     "item_id": row["item_id"],
                     "url": row["url"],
                     "domain": row["domain"],
                     "text": row["text"],
                     "saved_day": row["saved_day"],
                     "score": row["score"]})
    return data


def setup_fts():
    connection = get_connection()
    build_fts(connection, Strategy().strategy_info)
    total_chunks = connection.execute("SELECT count(*) as count FROM chunks_fts").fetchone()
    print(f"Total chunks in fts table: {total_chunks["count"]}")
    test_result = connection.execute("""
            SELECT item_id, bm25(chunks_fts) as bm25 FROM chunks_fts
            WHERE chunks_fts MATCH '"BCNF"' ORDER BY 2 LIMIT 3;
    """).fetchone()
    print(f"Item id: {test_result["item_id"]} BM25: {test_result["bm25"]}")
    connection.close()


if __name__ == '__main__':
    setup_fts()  # Rebuild chunks_fts

    test_result_1 = lexical_search("Why do programmers hate meetings in the afternoon?", 2)
    print(test_result_1)

    test_result_2 = lexical_search("stocks and bonds", 10, since=20261101, until=20261101)
    print(test_result_2)

    test_result_3 = lexical_search("stocks and bonds", 10, until=20261031)
    print(test_result_3)
