import os
import sqlite3
from typing import Optional

from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.environ.get("READLATER_DB", "data/readlater.db")


# Open a new connection on every call. No caching: a sqlite3 connection must
# stay in the thread that created it, and tests open several different paths.
def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn
