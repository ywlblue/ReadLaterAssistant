import datetime
import uuid

import chromadb
import pytest

from storage import connect
from tools import search_saved, list_saves

client = chromadb.EphemeralClient()
NEAR, MID, FAR = [1.0, 0, 0], [1.0, 1.0, 0], [0.3, 1.0, 0]


def fake_embed(texts):
    return [[1.0, 0.0, 0.0] for _ in texts]


@pytest.fixture
def conn(tmp_path):
    c = connect(str(tmp_path / "t.db"))
    yield c
    c.close()


def add_item(conn, item_id, title, domain="a.com", saved_at="2026-11-01T00:00:00+00:00"):
    conn.execute("INSERT INTO saved_items (id, url, normalized_url, domain, title, status, saved_at) "
                 "VALUES (?, ?, ?, ?, ?, 'digested', ?)",
                 (item_id, f"https://{domain}/{item_id}", f"{domain}/{item_id}", domain, title, saved_at))
    conn.commit()


@pytest.fixture
def collection():
    col = client.create_collection(f"t_{uuid.uuid4().hex}", metadata={"hnsw:space": "cosine"})
    yield col
    client.delete_collection(col.name)


def add_chunk(col, chunk_id, item_id, vec, domain="a.com", saved_day=20261101):
    col.add(ids=[chunk_id], documents=[f"text of {chunk_id}"], embeddings=[vec],
            metadatas=[{"item_id": item_id, "url": f"https://{domain}/{item_id}",
                        "domain": domain, "saved_day": saved_day}])


def test_dedup_same_item(conn, collection):
    add_item(conn, "A", "Title A")
    add_item(conn, "B", "Title B")
    add_chunk(collection, "a1", "A", NEAR)
    add_chunk(collection, "a2", "A", NEAR)
    add_chunk(collection, "b1", "B", MID)
    hits = search_saved(query="q", collection=collection, connection=conn, embed=fake_embed)
    assert [h.item_id for h in hits] == ["A", "B"]


def test_abstain_when_top_is_far(conn, collection):
    add_item(conn, "A", "Title A")
    add_chunk(collection, "a1", "A", FAR)
    assert search_saved(query="q", collection=collection, connection=conn, embed=fake_embed) == []


def test_list_saves_newest_first(conn):
    add_item(conn, "old", "Old", saved_at="2026-10-01T00:00:00+00:00")
    add_item(conn, "new", "New", saved_at="2026-11-01T00:00:00+00:00")
    assert [s.item_id for s in list_saves(conn)] == ["new", "old"]


def test_search_saved_order(conn, collection):
    add_item(conn, "A", "Title A")
    add_item(conn, "B", "Title B")
    add_chunk(collection, "a1", "A", MID)
    add_chunk(collection, "b1", "B", NEAR)
    assert [s.item_id for s in search_saved(query="q", collection=collection,
                                            connection=conn, embed=fake_embed)] == ["B", "A"]


def test_search_saved_max_k(conn, collection):
    for i in range(7):
        add_item(conn, str(i), f"Title {i}")
        add_chunk(collection, f"a{str(i)}", str(i), NEAR)
    assert len(search_saved(query="q", collection=collection,
                            connection=conn, embed=fake_embed)) == 5


def test_search_saved_skip_not_existed(conn, collection):
    add_item(conn, "A", "Title A")
    add_chunk(collection, "a1", "A", MID)
    add_chunk(collection, f"c1", "C", NEAR)
    assert [s.item_id for s in search_saved(query="q", collection=collection,
                                            connection=conn, embed=fake_embed)] == ["A"]


def test_search_saved_with_domain(conn, collection):
    add_item(conn, "A", "Title A", domain="a.com")
    add_chunk(collection, "a1", "A", MID, domain="a.com")
    add_item(conn, "B", "Title B", domain="b.com")
    add_chunk(collection, "b1", "B", MID, domain="b.com")
    result = search_saved(query="q", collection=collection,
                          connection=conn, embed=fake_embed, domain="b.com")
    assert len(result) == 1
    assert result[0].item_id == "B"


def test_search_saved_with_no_data(conn, collection):
    assert len(search_saved(query="q", collection=collection,
                            connection=conn, embed=fake_embed)) == 0


def test_list_save_with_domain(conn):
    add_item(conn, "A", "Title A", domain="a.com")
    add_item(conn, "B", "Title B", domain="b.com")
    result = list_saves(conn, domain="a.com")
    assert len(result) == 1
    assert result[0].item_id == "A"


def test_list_save_with_since(conn):
    add_item(conn, "A", "Old", saved_at="2026-10-01T00:00:00+00:00")
    add_item(conn, "B", "New", saved_at="2026-11-01T00:00:00+00:00")
    result = list_saves(conn, since=datetime.datetime(2026, 10, 30, tzinfo=datetime.timezone.utc))
    assert len(result) == 1
    assert result[0].item_id == "B"


def test_list_save_with_limit(conn):
    add_item(conn, "A", "T1", saved_at="2026-10-01T00:00:00+00:00")
    add_item(conn, "B", "T2", saved_at="2026-11-01T00:00:00+00:00")
    add_item(conn, "C", "T3", saved_at="2026-11-03T00:00:00+00:00")
    result = list_saves(conn, limit=2)
    assert len(result) == 2
    assert [s.item_id for s in result] == ["C", "B"]
