from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

import api
import db
from schemas import DigestParseError, SavedItemDigest


def test_save_empty_url(monkeypatch, tmp_path):
    mock_connect = Mock()
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))

    with TestClient(api.app) as client:
        response = client.post("/save", json={"url": ""})

    assert response.status_code == 400
    assert response.json() == {"detail": "Missing URL"}
    mock_connect.assert_not_called()


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


def test_save_llm_return_bad_json(monkeypatch):
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
        "error": "bad_json",
    }

    mock_save = Mock(return_value=(saved_item, False))
    mock_fetch = Mock()
    mock_digest = Mock(
        side_effect=DigestParseError(
            "bad_json",
            "LLM return invalid json",
            "This is a string",
        )
    )
    mock_record_digest = Mock(return_value=failed_item)

    monkeypatch.setattr(api, "connect", Mock(return_value=conn))
    monkeypatch.setattr(api, "save_item", mock_save)
    monkeypatch.setattr(api, "fetch_url", mock_fetch)
    monkeypatch.setattr(api, "digest", mock_digest)
    monkeypatch.setattr(api, "record_digest", mock_record_digest)

    with TestClient(api.app) as client:
        response = client.post(
            "/save",
            json={"url": saved_item["url"]},
        )

    assert response.status_code == 200
    save_response = api.SaveResponse.model_validate_json(response.text)
    assert save_response.error == "bad_json"
    assert save_response.title == "Test article"
    assert save_response.digest is None

    mock_record_digest.assert_called_once_with(
        conn,
        saved_item["id"],
        None,
        "bad_json",
    )
    mock_save.assert_called_once_with(conn, saved_item["url"])
    mock_fetch.assert_not_called()
    mock_digest.assert_called_once_with(saved_item["content_text"])
