import pytest

from storage import connect, count_items, save_item
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
