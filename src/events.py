import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from answers import Answer
from db import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS request_events (
    request_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    query_len INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    insufficient_evidence INTEGER NOT NULL,
    top_item_ids TEXT,          -- JSON string
    feedback TEXT,              -- 'FOUND' / 'MISSED' / NULL
    feedback_at TEXT
)
"""


def connect_events(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = get_connection(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def record_ask(conn: sqlite3.Connection, request_id: str, query_len: int, latency_ms: float, result: Answer):
    top_item_ids = list(dict.fromkeys(s.item_id for s in result.sources))
    cursor = conn.execute("INSERT OR IGNORE INTO request_events (request_id, created_at, query_len, latency_ms, "
                          "insufficient_evidence, top_item_ids) "
                          "VALUES (?, ?, ?, ?, ?, ?)",
                          (request_id, datetime.now(timezone.utc).isoformat(), query_len, latency_ms,
                           int(result.insufficient_evidence), json.dumps(top_item_ids)))
    conn.commit()
    created = cursor.rowcount == 1
    row = conn.execute("SELECT * FROM request_events WHERE request_id = ?", (request_id,)).fetchone()
    return row, created


def update_feedback(conn: sqlite3.Connection, request_id: str, feedback: str):
    cursor = conn.execute(
        "UPDATE request_events SET feedback = ?, feedback_at = ? WHERE request_id = ?",
        (feedback, datetime.now(timezone.utc).isoformat(), request_id)
    )
    conn.commit()
    updated = cursor.rowcount == 1
    row = conn.execute("SELECT * FROM request_events WHERE request_id = ?", (request_id,)).fetchone()
    return row, updated
