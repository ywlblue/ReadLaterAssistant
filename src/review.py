import sqlite3
from datetime import datetime, timedelta

from db import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS item_opens (
    item_id   TEXT NOT NULL,
    opened_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS review_recommendations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id     TEXT NOT NULL,
    item_id        TEXT NOT NULL,
    recommended_at TEXT NOT NULL
);
"""
POOL_SIZE, MAX_PICKS, COOLDOWN_DAYS = 30, 3, 14


def connect_review(db_path=None):
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def select_review(conn, now: datetime) -> list[sqlite3.Row]:
    cutoff = (now - timedelta(days=COOLDOWN_DAYS)).isoformat()
    return conn.execute("""
        WITH pool AS (
            SELECT id, title, url, saved_at, digest_json FROM saved_items
            WHERE status = 'digested'
            ORDER BY saved_at DESC, id ASC LIMIT ?
        )
        SELECT * FROM pool
        WHERE id NOT IN (SELECT item_id FROM item_opens)
          AND id NOT IN (SELECT item_id FROM review_recommendations
                         WHERE recommended_at >= ?)
        ORDER BY saved_at ASC, id ASC LIMIT ?
    """, (POOL_SIZE, cutoff, MAX_PICKS)).fetchall()


def record_review(conn, request_id: str, item_ids: list[str], now: datetime):
    if isinstance(item_ids, str):
        raise TypeError("Invalid item_ids. Should be a list of string. Received string instead.")
    with conn:
        conn.executemany(
            "INSERT INTO review_recommendations (request_id, item_id, recommended_at) VALUES (?, ?, ?)",
            [(request_id, i, now.isoformat()) for i in item_ids])


def record_opened(conn, item_id: str, now: datetime):
    with conn:
        row = conn.execute("SELECT * FROM saved_items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise ValueError("Item id not found")
        conn.execute("INSERT INTO item_opens (item_id, opened_at) VALUES (? , ?)",
                     (item_id, now.isoformat()))
