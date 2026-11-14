import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from answers import Answer
from db import get_connection
from tools import SearchHit

SCHEMA = """
CREATE TABLE IF NOT EXISTS request_events (
    request_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    query_len INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    insufficient_evidence INTEGER NOT NULL,
    top_item_ids TEXT,          -- JSON string
    feedback TEXT,              -- 'FOUND' / 'MISSED' / NULL
    feedback_at TEXT,
    kind TEXT NOT NULL DEFAULT 'ask'
)
"""


def run_migration(conn):
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(request_events)")}
    if "kind" not in cols:
        conn.execute("ALTER TABLE request_events ADD COLUMN kind TEXT NOT NULL DEFAULT 'ask'")


def connect_events(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = get_connection(db_path)
    conn.execute(SCHEMA)
    run_migration(conn)
    conn.commit()
    return conn


def record_request(conn, request_id, kind, query_len, latency_ms,
                   no_result: bool, top_item_ids: list[str]):
    conn.execute("INSERT OR IGNORE INTO request_events (request_id, kind, created_at, query_len, "
                 "latency_ms, insufficient_evidence, top_item_ids) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (request_id, kind, datetime.now(timezone.utc).isoformat(), query_len,
                  latency_ms, int(no_result), json.dumps(top_item_ids)))
    conn.commit()


def record_ask(conn, request_id, query_len, latency_ms, result: Answer):
    ids = list(dict.fromkeys(s.item_id for s in result.sources))
    record_request(conn, request_id, "ask", query_len, latency_ms, result.insufficient_evidence, ids)


def record_find(conn, request_id, query_len, latency_ms, hits: list[SearchHit]):
    record_request(conn, request_id, "find", query_len, latency_ms, not hits, [h.item_id for h in hits])


def update_feedback(conn: sqlite3.Connection, request_id: str, feedback: str):
    cursor = conn.execute(
        "UPDATE request_events SET feedback = ?, feedback_at = ? WHERE request_id = ?",
        (feedback, datetime.now(timezone.utc).isoformat(), request_id)
    )
    conn.commit()
    updated = cursor.rowcount == 1
    row = conn.execute("SELECT * FROM request_events WHERE request_id = ?", (request_id,)).fetchone()
    return row, updated
