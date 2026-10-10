import pytest

from urls import InvalidUrlError, make_item_id, normalize_url


@pytest.mark.parametrize("raw", [
    "https://a.com/post",
    "https://a.com/post/",
    "HTTPS://A.com/post",
    "https://a.com:443/post",
    "https://a.com/post?utm_source=x&fbclid=123",
    "https://a.com/post#section-2",
    "  https://a.com/post  ",
])
def test_variants_normalize_to_the_same_url(raw):
    assert normalize_url(raw) == "https://a.com/post"


def test_real_query_params_are_kept_and_sorted():
    assert normalize_url("https://a.com/s?q=llm&page=2") == "https://a.com/s?page=2&q=llm"


def test_different_pages_stay_different():
    assert normalize_url("https://a.com/post?id=1") != normalize_url("https://a.com/post?id=2")


@pytest.mark.parametrize("raw", ["", "hello", "a.com/post", "ftp://a.com/x", "https://", "https://a.com:99999/x"])
def test_bad_input_gives_controlled_error(raw):
    with pytest.raises(InvalidUrlError):
        normalize_url(raw)


def test_item_id_is_stable():
    assert make_item_id("https://a.com/post") == make_item_id("https://a.com/post")
    assert len(make_item_id("https://a.com/post")) == 16

