from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

import api
from fetch import FetchResult
from schemas import DigestParseError, SavedItemDigest
from events import connect_events
from review import connect_review
from storage import connect, save_item, record_digest


def test_save_empty_url(monkeypatch, tmp_path):
    conn = Mock()
    monkeypatch.setattr(api, "connect", Mock(return_value=conn))

    with TestClient(api.app) as client:
        response = client.post("/save", json={"url": ""})

    assert response.status_code == 400
    assert response.json() == {"detail": "Missing URL"}

    conn.assert_not_called()


@pytest.fixture
def save_context(monkeypatch):
    conn = Mock()

    summary = SavedItemDigest(
        summary="An article about testing FastAPI endpoints.",
        tags=["python", "fastapi", "testing"],
        content_type="article",
    )

    saved_item = {
        "id": "item-123",
        "url": "https://example.com/article",
        "title": "Test article",
        "content_text": "Some article content.",
        "digest_json": None,
        "status": "fetched",
        "error": None,
    }

    digested_item = {
        **saved_item,
        "digest_json": summary.model_dump_json(),
        "status": "digested",
    }

    mock_save = Mock(return_value=(saved_item, False))
    mock_fetch = Mock()
    mock_digest = Mock(return_value=summary)
    mock_record_digest = Mock(return_value=digested_item)

    monkeypatch.setattr(api, "connect", Mock(return_value=conn))
    monkeypatch.setattr(api, "save_item", mock_save)
    monkeypatch.setattr(api, "fetch_url", mock_fetch)
    monkeypatch.setattr(api, "digest", mock_digest)
    monkeypatch.setattr(api, "record_digest", mock_record_digest)

    with TestClient(api.app) as client:
        yield SimpleNamespace(
            client=client,
            conn=conn,
            summary=summary,
            saved_item=saved_item,
            digested_item=digested_item,
            mock_save=mock_save,
            mock_fetch=mock_fetch,
            mock_digest=mock_digest,
            mock_record_digest=mock_record_digest,
        )


def test_save_digest_success(save_context):
    ctx = save_context

    response = ctx.client.post(
        "/save",
        json={"url": ctx.saved_item["url"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "item_id": ctx.saved_item["id"],
        "url": ctx.saved_item["url"],
        "title": ctx.saved_item["title"],
        "digest": ctx.summary.model_dump(mode="json"),
        "status": ctx.digested_item["status"],
        "error": None,
        "warning": None,
    }

    ctx.mock_digest.assert_called_once_with(
        ctx.saved_item["content_text"]
    )
    ctx.mock_record_digest.assert_called_once_with(
        ctx.conn,
        ctx.saved_item["id"],
        ctx.summary,
        None,
    )
    ctx.mock_fetch.assert_not_called()


def test_save_reuses_existing_digest(save_context):
    ctx = save_context

    ctx.mock_save.side_effect = [
        (ctx.saved_item, False),
        (ctx.digested_item, False),
    ]

    payload = {"url": ctx.saved_item["url"]}

    first_response = ctx.client.post("/save", json=payload)
    second_response = ctx.client.post("/save", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["digest"] == (
        ctx.summary.model_dump(mode="json")
    )
    assert second_response.json() == first_response.json()

    assert ctx.mock_save.call_count == 2
    ctx.mock_digest.assert_called_once_with(
        ctx.saved_item["content_text"]
    )
    ctx.mock_record_digest.assert_called_once_with(
        ctx.conn,
        ctx.saved_item["id"],
        ctx.summary,
        None,
    )
    ctx.mock_fetch.assert_not_called()


def test_save_llm_return_invalid_json(monkeypatch):
    conn = Mock()

    saved_item = {
        "id": "item-123",
        "url": "https://example.com/article",
        "title": "Test article",
        "content_text": "Some article content.",
        "digest_json": None,
        "status": "fetched",
        "error": None,
    }

    failed_item = {
        **saved_item,
        "status": "digest_failed",
        "error": "invalid_json",
    }

    snapshot_path = f"{saved_item['id']}.html"

    mock_save = Mock(return_value=(saved_item, False))
    mock_fetch = Mock()
    mock_save_snapshot = Mock(return_value=snapshot_path)
    mock_digest = Mock(
        side_effect=DigestParseError(
            "invalid_json",
            "LLM return invalid json",
            "This is a string",
        )
    )
    mock_record_digest = Mock(return_value=failed_item)

    monkeypatch.setattr(api, "connect", Mock(return_value=conn))
    monkeypatch.setattr(api, "save_item", mock_save)
    monkeypatch.setattr(api, "fetch_url", mock_fetch)
    monkeypatch.setattr(api, "save_snapshot", mock_save_snapshot)
    monkeypatch.setattr(api, "digest", mock_digest)
    monkeypatch.setattr(api, "record_digest", mock_record_digest)

    with TestClient(api.app) as client:
        response = client.post(
            "/save",
            json={"url": saved_item["url"], "origin_type": "ORIGINAL"},
        )

    assert response.status_code == 200
    save_response = api.SaveResponse.model_validate_json(response.text)
    assert save_response.error == "invalid_json"
    assert save_response.title == "Test article"
    assert save_response.digest is None

    mock_record_digest.assert_called_once_with(
        conn,
        saved_item["id"],
        None,
        "invalid_json",
    )
    mock_save.assert_called_once_with(conn, saved_item["url"], api.SavedAtOrigin.ORIGINAL.name)
    mock_fetch.assert_not_called()
    mock_save_snapshot.assert_not_called()
    mock_digest.assert_called_once_with(saved_item["content_text"])


def test_save_content(monkeypatch, tmp_path):
    fetch_result = FetchResult(True, "Hello World", "This is a text")
    snapshot_path = f"test-abcd.html"
    mock_fetch = Mock(return_value=fetch_result)
    mock_save_snapshot = Mock(return_value=snapshot_path)
    mock_digest = Mock(
        side_effect=DigestParseError(
            "bad_json",
            "LLM return invalid json",
            "This is a string",
        )
    )

    # Return lambda for connection instead of using pre-initialized connection
    monkeypatch.setattr(api, "connect", lambda: connect(str(tmp_path / "test.db")))
    monkeypatch.setattr(api, "fetch_url", mock_fetch)
    monkeypatch.setattr(api, "save_snapshot", mock_save_snapshot)
    monkeypatch.setattr(api, "digest", mock_digest)

    with TestClient(api.app) as client:
        response = client.post("/save", json={"url": "https://example.com/article", "origin_type": "IMPORT"})

    assert response.status_code == 200
    save_response = api.SaveResponse.model_validate_json(response.text)
    assert save_response.error == "bad_json"
    assert save_response.title == "Hello World"
    assert save_response.digest is None

    assert save_response.item_id is not None
    saved_item = connect(str(tmp_path / "test.db")).execute("SELECT * FROM saved_items WHERE id = ?",
                                                            (save_response.item_id,)).fetchone()
    assert saved_item["content_text"] == "This is a text"
    assert saved_item["status"] == "digest_failed"
    assert saved_item["saved_at_origin"] == "IMPORT"
    assert saved_item["snapshot_path"] == snapshot_path
    mock_fetch.assert_called_once()


@pytest.fixture
def review_context(monkeypatch, tmp_path):
    """Real SQLite in tmp_path, seeded with 2 digested items and 1 digest_failed item.
    The LLM is never called: api.review_reason is replaced by a fake."""
    db_path = str(tmp_path / "test.db")
    connect(db_path)  # saved_items table
    connect_events(db_path)  # request_events table (+ kind migration)
    conn = connect_review(db_path)

    digest = SavedItemDigest(summary="A post about caching.",
                             tags=["cache", "backend", "scale"], content_type="article")
    seeded = []
    for url in ["https://a.com/one", "https://b.com/two"]:
        item, _ = save_item(conn, url)
        record_digest(conn, item["id"], digest, None)
        seeded.append(item["id"])
    failed, _ = save_item(conn, "https://c.com/broken")
    record_digest(conn, failed["id"], None, "schema_error")  # must never be picked
    conn.close()

    monkeypatch.setattr(api, "connect_review", lambda: connect_review(db_path))
    monkeypatch.setattr(api, "review_reason", lambda row: f"fake reason for {row['id']}")

    with TestClient(api.app) as client:
        yield SimpleNamespace(client=client, db_path=db_path, seeded=seeded,
                              failed_id=failed["id"])


def test_review_returns_digested_items(review_context):
    ctx = review_context
    response = ctx.client.post("/review")

    assert response.status_code == 200
    body = response.json()
    assert sorted(p["item_id"] for p in body["picks"]) == sorted(ctx.seeded)
    assert all(p["reason"] == f"fake reason for {p['item_id']}" for p in body["picks"])

    conn = connect_review(ctx.db_path)
    history = conn.execute("SELECT item_id FROM review_recommendations WHERE request_id = ?",
                           (body["request_id"],)).fetchall()
    event = conn.execute("SELECT kind FROM request_events WHERE request_id = ?",
                         (body["request_id"],)).fetchone()
    conn.close()
    assert sorted(r["item_id"] for r in history) == sorted(ctx.seeded)
    assert event["kind"] == "review"


def test_review_second_call_respects_cooldown(review_context):
    ctx = review_context
    ctx.client.post("/review")
    response = ctx.client.post("/review")

    assert response.status_code == 200
    assert response.json()["picks"] == []


def test_review_empty_db_returns_zero_picks(monkeypatch, tmp_path):
    db_path = str(tmp_path / "empty.db")
    connect(db_path)
    connect_events(db_path)
    monkeypatch.setattr(api, "connect_review", lambda: connect_review(db_path))

    with TestClient(api.app) as client:
        response = client.post("/review")

    assert response.status_code == 200
    assert response.json()["picks"] == []

    conn = connect_review(db_path)
    event = conn.execute("SELECT kind, insufficient_evidence FROM request_events").fetchone()
    conn.close()
    assert event["kind"] == "review"
    assert event["insufficient_evidence"] == 1


def test_opened_with_valid_id(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    row, _ = save_item(conn, "https://example.com/article")
    conn.close()
    monkeypatch.setattr(api, "connect_review", lambda: connect_review(db_path))

    with TestClient(api.app) as client:
        response = client.post("/opened", json={"item_id": row["id"]})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_opened_with_invalid_id(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = connect(db_path)
    row, _ = save_item(conn, "https://example.com/article")
    conn.close()
    monkeypatch.setattr(api, "connect_review", lambda: connect_review(db_path))

    with TestClient(api.app) as client:
        response = client.post("/opened", json={"item_id": "fake12345"})

    assert response.status_code == 404


def test_startup_creates_tables():
    """No setup at all: lifespan alone must create the tables in the default DB."""
    with TestClient(api.app) as client:
        response = client.post("/review")

    assert response.status_code == 200
    assert response.json()["picks"] == []

