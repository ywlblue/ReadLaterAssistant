from chunks import connect_chunks
from events import connect_events
from review import connect_review
from storage import connect


def init_db(db_path=None):
    """Create every table once. Safe to run again (CREATE TABLE IF NOT EXISTS)."""
    for connect_fn in (connect, connect_chunks, connect_events, connect_review):
        connect_fn(db_path).close()
