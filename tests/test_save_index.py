import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import chromadb
import pytest
from starlette.testclient import TestClient

import api
import chunks
import index
from fetch import FetchResult
from schemas import SavedItemDigest, DigestParseError
from storage import connect

URL = "https://example.com/henry-viii"
# Longer than chunk_size (1000) so it splits into several chunks
TEXT = "\n\n".join(
    f"Paragraph {i}: Henry VIII had six wives and broke with Rome. " * 8
    for i in range(6)
)


def fake_embed(texts):
    return [[0.1, 0.2, 0.3] for _ in texts]


@pytest.fixture
def ctx(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")

    # Point api and process_document at the same temp DB
    monkeypatch.setattr(api, "connect", lambda: connect(db_path))
    real_connect_chunks = chunks.connect_chunks
    monkeypatch.setattr(chunks, "connect_chunks", lambda db=None: real_connect_chunks(db_path))

    # In-memory Chroma, fresh collection per test
    collection = chromadb.EphemeralClient().get_or_create_collection(
        f"test_{uuid.uuid4().hex}", metadata={"hnsw:space": "cosine"}
    )
    monkeypatch.setattr(api, "chroma_collection", collection)

    # Real build_index, fake embed
    embed = Mock(side_effect=fake_embed)
    real_build_index = index.build_index
    monkeypatch.setattr(
        api, "build_index",
        lambda coll, conn, item_id=None: real_build_index(coll, conn, embed=embed, item_id=item_id),
    )

    fetch = Mock(return_value=FetchResult(True, "Henry VIII", TEXT))
    digest = Mock(return_value=SavedItemDigest(
        summary="About Henry VIII.", tags=["history", "england", "tudor"], content_type="article",
    ))
    monkeypatch.setattr(api, "fetch_url", fetch)
    monkeypatch.setattr(api, "save_snapshot", Mock(return_value="snap.html"))
    monkeypatch.setattr(api, "digest", digest)

    with TestClient(api.app) as client:
        yield SimpleNamespace(
            client=client, db_path=db_path, collection=collection,
            embed=embed, fetch=fetch, digest=digest,
        )


def chroma_ids(collection, item_id):
    return collection.get(where={"item_id": item_id})["ids"]


def sqlite_chunk_count(db_path, item_id):
    conn = connect(db_path)
    chunks.connect_chunks()  # make sure the chunks table exists
    return conn.execute("SELECT COUNT(*) FROM chunks WHERE item_id = ?", (item_id,)).fetchone()[0]


def test_new_save_is_chunked_and_indexed(ctx):
    response = ctx.client.post("/save", json={"url": URL})

    assert response.status_code == 200
    body = api.SaveResponse.model_validate_json(response.text)
    assert body.warning is None

    ids = chroma_ids(ctx.collection, body.item_id)
    assert len(ids) > 1                                   # split into several chunks
    assert len(ids) == sqlite_chunk_count(ctx.db_path, body.item_id)
    ctx.embed.assert_called()


def test_duplicate_save_does_not_reindex(ctx):
    first = ctx.client.post("/save", json={"url": URL}).json()
    count_after_first = ctx.collection.count()
    embed_calls_after_first = ctx.embed.call_count

    second = ctx.client.post("/save", json={"url": URL}).json()

    assert second["item_id"] == first["item_id"]
    assert ctx.collection.count() == count_after_first   # chunk count unchanged
    assert ctx.embed.call_count == embed_calls_after_first  # no new embedding call
    ctx.fetch.assert_called_once()


def test_embed_error_keeps_item_and_returns_warning(ctx):
    ctx.embed.side_effect = RuntimeError("embedding API down")

    response = ctx.client.post("/save", json={"url": URL})

    assert response.status_code == 200                   # index failure must not fail the save
    body = api.SaveResponse.model_validate_json(response.text)
    assert body.warning == "Indexing failed."
    assert ctx.collection.count() == 0

    row = connect(ctx.db_path).execute(
        "SELECT content_text, status FROM saved_items WHERE id = ?", (body.item_id,)
    ).fetchone()
    assert row["content_text"] == TEXT                    # item is kept
    assert row["status"] == "digested"                    # digest unaffected by index failure


def test_digest_error_still_indexed(ctx):
    ctx.digest.side_effect = DigestParseError("invalid_json", "bad", "x")

    response = ctx.client.post("/save", json={"url": URL})

    body = api.SaveResponse.model_validate_json(response.text)
    assert body.error == "invalid_json"
    assert body.warning is None
    assert len(chroma_ids(ctx.collection, body.item_id)) > 0  # chunks come from the text, not the digest
