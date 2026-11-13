from datetime import datetime, timedelta, timezone
import uuid

import pytest

from fetch import FetchResult
from review import connect_review, select_review, record_review, record_opened
from storage import connect, save_item, record_digest, record_fetch


def test_select_review_with_empty_db(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))
    result = select_review(conn, datetime.now())
    assert result == []


def test_select_review_not_return_opened_items(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))
    item, _ = save_item(conn, "https://abc.com/opened")
    record_opened(conn, item["id"], datetime.now(timezone.utc))
    item = record_digest(conn, item["id"], None, None)
    conn.commit()
    assert item["status"] == "digested"
    result = select_review(conn, datetime.now(timezone.utc))
    assert result == []
    conn.close()


def test_select_review_not_return_digested_failed(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))
    item_1, _ = save_item(conn, "https://abc.com/x")
    item_2, _ = save_item(conn, "https://cdf.com/y")
    item_1 = record_digest(conn, item_1["id"], None, "Some errors occurred")
    item_2 = record_digest(conn, item_2["id"], None, None)
    conn.commit()
    assert item_1["status"] == "digest_failed"
    assert item_2["status"] == "digested"
    result = select_review(conn, datetime.now(timezone.utc))
    assert len(result) == 1
    assert result[0]["id"] == item_2["id"]
    conn.close()


def test_select_review_not_return_fetched(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))
    item_1, _ = save_item(conn, "https://abc.com/x")
    item_2, _ = save_item(conn, "https://cdf.com/y")
    item_1 = record_digest(conn, item_1["id"], None, None)
    item_2 = record_fetch(conn, item_2["id"], FetchResult(title="This is a title", text="This is a text",
                                                          content_sha256="sha256", ok=True), None)
    conn.commit()
    assert item_1["status"] == "digested"
    assert item_2["status"] == "fetched"
    result = select_review(conn, datetime.now(timezone.utc))
    assert len(result) == 1
    assert result[0]["id"] == item_1["id"]
    conn.close()


def test_select_review_with_pool_size(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))

    oldest_item_1, _ = save_item(conn, "https://old1.com")
    oldest_item_1 = record_digest(conn, oldest_item_1["id"], None, None)
    assert oldest_item_1["status"] == "digested"

    oldest_item_2, _ = save_item(conn, "https://old2.com")
    oldest_item_2 = record_digest(conn, oldest_item_2["id"], None, None)
    assert oldest_item_2["status"] == "digested"

    for i in range(30):
        identifier = uuid.uuid4()
        item, created = save_item(conn, f"https://{identifier}.com/{i}")
        item = record_digest(conn, item["id"], None, None)
        assert item["status"] == "digested"
    result = select_review(conn, datetime.now(timezone.utc))
    assert len(result) == 3
    all_ids = [row["id"] for row in result]
    assert oldest_item_1["id"] not in all_ids
    assert oldest_item_2["id"] not in all_ids
    conn.close()


def test_select_review_with_day_restriction(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))

    item_1, _ = save_item(conn, f"https://test1.com/abc")
    record_digest(conn, item_1["id"], None, None)
    record_review(conn, "req1", [item_1["id"]], datetime.now(timezone.utc) - timedelta(15))

    item_2, _ = save_item(conn, f"https://test2.com/cde")
    record_digest(conn, item_2["id"], None, None)
    record_review(conn, "req2", [item_2["id"]], datetime.now(timezone.utc) - timedelta(13))

    result = select_review(conn, datetime.now(timezone.utc))
    assert len(result) == 1
    assert result[0]["id"] == item_1["id"]

    conn.close()


def test_select_review_conn_reset_diff_result(tmp_path):
    db_path = str(tmp_path / "test.db")
    connect(db_path)
    conn = connect_review(str(tmp_path / "test.db"))

    for i in range(6):
        identifier = uuid.uuid4()
        item, created = save_item(conn, f"https://{identifier}.com/{i}")
        item = record_digest(conn, item["id"], None, None)
        assert item["status"] == "digested"

    now = datetime.now(timezone.utc)
    picks = select_review(conn, now)
    assert len(picks) == 3

    record_review(conn, "r1", [r["id"] for r in picks], now)

    conn.close()

    conn = connect_review(db_path)
    again = select_review(conn, now)
    assert len(again) == 3

    assert not set(r["id"] for r in picks) & set(r["id"] for r in again)


def test_select_review_call_twice_same_result(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))

    for i in range(6):
        identifier = uuid.uuid4()
        item, created = save_item(conn, f"https://{identifier}.com/{i}")
        item = record_digest(conn, item["id"], None, None)
        assert item["status"] == "digested"
    result_1 = select_review(conn, datetime.now(timezone.utc))
    assert len(result_1) == 3

    result_2 = select_review(conn, datetime.now(timezone.utc))
    assert len(result_2) == 3

    assert result_1 == result_2
    conn.close()


def test_record_review_with_invalid_item_ids(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))
    with pytest.raises(TypeError):
        record_review(conn, "r", "abc", datetime.now(timezone.utc))


def test_record_opened_non_exist_item_id(tmp_path):
    connect(str(tmp_path / "test.db"))
    conn = connect_review(str(tmp_path / "test.db"))
    with pytest.raises(ValueError):
        record_opened(conn, "123", datetime.now(timezone.utc))
