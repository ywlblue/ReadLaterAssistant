from readlater.db import get_connection
from readlater.init_db import init_db


def test_init_db_creates_all_tables(tmp_path):
    path = str(tmp_path / "init.db")
    init_db(path)
    init_db(path)  # run twice: must not fail

    conn = get_connection(path)
    names = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    assert {"saved_items", "chunks", "request_events",
            "item_opens", "review_recommendations"} <= names
