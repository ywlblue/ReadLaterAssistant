import hashlib
import logging
import sqlite3

import requests

from fetch import download
from logging_config import setup_logging
from storage import connect, save_snapshot

logger = logging.getLogger(__name__)


def backfill_snapshot(conn: sqlite3.Connection):
    snapshot_rows = conn.execute("SELECT * FROM saved_items "
                                 "WHERE content_text IS NOT NULL AND "
                                 "snapshot_path IS NULL").fetchall()
    status_map = {"success": 0, "failed": 0}
    for row in snapshot_rows:
        url = row["url"]
        try:
            page = download(url)
            if page.status_code == 200:
                snapshot_path = save_snapshot(row["id"], page.body)
                conn.execute(
                    "UPDATE saved_items SET snapshot_path = ? WHERE id = ?",
                    (snapshot_path, row["id"]))
                conn.commit()
                status_map["success"] += 1
            else:
                logger.log(logging.ERROR, f"Failed to download url {url}. Error code: {page.status_code}")
                status_map["failed"] += 1
        except requests.RequestException as e:
            logger.log(logging.ERROR, f"Failed to download url {url}. Error: {str(e)}")
            status_map["failed"] += 1
    logger.log(logging.INFO, f"Snapshot backfill status: success {status_map['success']}, "
                             f"failed {status_map['failed']}")


def backfill_sha(conn: sqlite3.Connection):
    sha_rows = conn.execute("SELECT * FROM saved_items "
                            "WHERE content_text IS NOT NULL").fetchall()

    for row in sha_rows:
        conn.execute(
            "UPDATE saved_items SET content_sha256 = ? WHERE id = ?",
            (hashlib.sha256(row["content_text"].encode()).hexdigest(), row["id"])
        )
        conn.commit()


if __name__ == '__main__':
    setup_logging()

    conn_storage = connect()
    backfill_snapshot(conn_storage)
    backfill_sha(conn_storage)
    conn_storage.close()
