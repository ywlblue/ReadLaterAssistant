import os
import sqlite3
from datetime import datetime, timezone

from urls import domain_of, make_item_id, normalize_url

SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_items (
    id             TEXT PRIMARY KEY,
    url            TEXT NOT NULL,
    normalized_url TEXT NOT NULL UNIQUE,
    domain         TEXT NOT NULL,
    title          TEXT,
    content_text   TEXT,
    digest_json    TEXT,
    status         TEXT NOT NULL DEFAULT 'saved',
    error          TEXT,
    saved_at       TEXT NOT NULL
)
"""


def connect(db_path: str) -> sqlite3.Connection:
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def save_item(conn: sqlite3.Connection, url: str):
    normalized = normalize_url(url)
    item_id = make_item_id(normalized)
    cursor = conn.execute(
        "INSERT OR IGNORE INTO saved_items (id, url, normalized_url, domain, saved_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (item_id, url.strip(), normalized, domain_of(normalized),
         datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    created = cursor.rowcount == 1
    row = conn.execute("SELECT * FROM saved_items WHERE id = ?", (item_id,)).fetchone()
    return row, created


def count_items(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM saved_items").fetchone()[0]

