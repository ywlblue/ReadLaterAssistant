import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from db import get_connection
from fetch import FetchResult
from schemas import SavedItemDigest
from urls import domain_of, make_item_id, normalize_url

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "snapshots"

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
    saved_at       TEXT NOT NULL,
    saved_at_origin TEXT,
    snapshot_path TEXT,
    content_sha256 TEXT
)
"""


def run_migration(conn: sqlite3.Connection):
    new_columns = [("saved_at_origin", "TEXT"), ("snapshot_path", "TEXT"), ("content_sha256", "TEXT")]
    rows = conn.execute("PRAGMA table_info(saved_items)").fetchall()
    existing_columns = set(row["name"] for row in rows)
    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            conn.execute(f"ALTER TABLE saved_items ADD COLUMN {col_name} {col_type};")


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = get_connection(db_path)
    conn.execute(SCHEMA)
    run_migration(conn)
    conn.commit()
    return conn


# Save url related information
def save_item(conn: sqlite3.Connection, url: str, origin_type: str = 'LIVE'):
    normalized = normalize_url(url)
    item_id = make_item_id(normalized)
    cursor = conn.execute(
        "INSERT OR IGNORE INTO saved_items (id, url, normalized_url, domain, saved_at, saved_at_origin) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (item_id, url.strip(), normalized, domain_of(normalized),
         datetime.now(timezone.utc).isoformat(), origin_type),
    )
    conn.commit()
    created = cursor.rowcount == 1
    row = conn.execute("SELECT * FROM saved_items WHERE id = ?", (item_id,)).fetchone()
    return row, created


def count_items(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM saved_items").fetchone()[0]


def record_fetch(conn: sqlite3.Connection, item_id: str, result: FetchResult, snapshot_path: Optional[str] = None):
    if result.ok:
        conn.execute(
            "UPDATE saved_items SET title = ?, content_text = ?, status = 'fetched', error = NULL, "
            "snapshot_path = ?, content_sha256 = ? "
            "WHERE id = ?",
            (result.title, result.text, snapshot_path, result.content_sha256, item_id)
        )
    else:
        conn.execute(
            "UPDATE saved_items SET status = 'fetch_failed', error = ? WHERE id = ?",
            (result.error, item_id),
        )
    conn.commit()
    return conn.execute("SELECT * FROM saved_items WHERE id = ?", (item_id,)).fetchone()


def record_digest(conn: sqlite3.Connection, item_id: str, result: Optional[SavedItemDigest],
                  err_msg: Optional[str] = None):
    conn.execute(
        "UPDATE saved_items SET digest_json = ?, status = ?, error = ? "
        "WHERE id = ?",
        (result.model_dump_json() if result else None,
         "digested" if not err_msg else "digest_failed",
         err_msg
         , item_id)
    )
    conn.commit()
    return conn.execute("SELECT * FROM saved_items WHERE id = ?", (item_id,)).fetchone()


def save_snapshot(item_id: str, snapshot: bytes, folder: Path = SNAPSHOT_PATH) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{item_id}.html"
    (folder / filename).write_bytes(snapshot)
    return filename

