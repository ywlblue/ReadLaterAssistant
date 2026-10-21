import pytest

from storage import connect, count_items, save_item, save_snapshot
from urls import InvalidUrlError


def test_same_url_twice_gives_same_id_and_one_row(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    first, created_first = save_item(conn, "https://a.com/post?utm_source=x")
    second, created_second = save_item(conn, "https://a.com/post")
    assert created_first is True
    assert created_second is False
    assert first["id"] == second["id"]
    assert count_items(conn) == 1


def test_items_survive_reopening_the_database(tmp_path):
    path = str(tmp_path / "test.db")
    conn = connect(path)
    item, _ = save_item(conn, "https://a.com/post")
    conn.close()

    again, created = save_item(connect(path), "https://a.com/post")
    assert created is False
    assert again["id"] == item["id"]


def test_bad_url_is_not_stored(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    with pytest.raises(InvalidUrlError):
        save_item(conn, "not a url")
    assert count_items(conn) == 0


def test_save_diff_origin_type(tmp_path):
    test_url = "https://test-diff-origin.com/chpt1"
    conn = connect(str(tmp_path / "test.db"))

    saved_item_live, created_live = save_item(conn, test_url)
    assert saved_item_live["saved_at_origin"] == "LIVE"
    assert created_live

    saved_item_import, created_import = save_item(conn, test_url, "IMPORT")
    assert not created_import
    assert saved_item_import["saved_at_origin"] == "LIVE"
    assert saved_item_import["id"] == saved_item_live["id"]
    assert saved_item_import["saved_at"] == saved_item_live["saved_at"]


def test_save_snapshot(tmp_path):
    test_url = "https://test-snapshot-saving.com/item/01"
    conn = connect(str(tmp_path / "test.db"))

    saved_item, created = save_item(conn, test_url)
    assert created
    assert saved_item["id"]

    test_snapshot_path = tmp_path
    test_data = b"<html>hi</html>"
    snapshot_path = save_snapshot(saved_item["id"], test_data, test_snapshot_path)
    assert snapshot_path == f"{saved_item["id"]}.html"
    assert (tmp_path / snapshot_path).read_bytes() == test_data
