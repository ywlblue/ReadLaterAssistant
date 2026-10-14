from pathlib import Path

import pytest
import requests

from fetch import MAX_BYTES, Page, fetch_url
from storage import connect, record_fetch, save_item

FIXTURES = Path(__file__).parent / "fixtures"


def fake_page(status_code, filename=None, body=b""):
    if filename:
        body = (FIXTURES / filename).read_bytes()
    return lambda url: Page(status_code, "text/html; charset=utf-8", body)


def fake_timeout(url):
    raise requests.Timeout("fake timeout")


CASES = [
    ("valid", fake_page(200, "valid.html"), None),
    ("not_found", fake_page(404, "not_found.html"), "http_404"),
    ("paywall_preview", fake_page(200, "paywall.html"), "too_little_text"),
    ("oversize", fake_page(200, body=b"x" * (MAX_BYTES + 1)), "too_large"),
    ("timeout", fake_timeout, "timeout"),
]


@pytest.mark.parametrize("name, download, expected_error", CASES, ids=[c[0] for c in CASES])
def test_each_fixture_has_a_controlled_outcome(name, download, expected_error):
    result = fetch_url("https://a.com/post", download_page=download)
    if expected_error is None:
        assert result.ok is True
        assert result.error is None
    else:
        assert result.ok is False
        assert result.error.startswith(expected_error)
        assert result.text is None


def test_valid_page_keeps_article_text_and_drops_noise():
    result = fetch_url("https://a.com/post", download_page=fake_page(200, "valid.html"))
    assert result.title == "How SQLite Stores Rows"
    assert "SQLite keeps every table in a B-tree" in result.text
    assert "中文也要能正常保存" in result.text
    assert "Subscribe" not in result.text
    assert "tracking code" not in result.text
    assert "Copyright" not in result.text


def test_fetched_text_survives_reopening_the_database(tmp_path):
    path = str(tmp_path / "test.db")
    conn = connect(path)
    item, _ = save_item(conn, "https://a.com/post")
    record_fetch(conn, item["id"], fetch_url(item["url"], download_page=fake_page(200, "valid.html")))
    conn.close()

    again, created = save_item(connect(path), "https://a.com/post")
    assert created is False
    assert again["status"] == "fetched"
    assert again["title"] == "How SQLite Stores Rows"
    assert "B-tree" in again["content_text"]


def test_failed_fetch_is_recorded_and_stays_visible(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    item, _ = save_item(conn, "https://a.com/gone")
    row = record_fetch(conn, item["id"], fetch_url(item["url"], download_page=fake_page(404, "not_found.html")))
    assert row["status"] == "fetch_failed"
    assert row["error"] == "http_404"
    assert row["content_text"] is None
