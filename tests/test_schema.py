import pytest

from schemas import DigestParseError, SavedItemDigest, parse_digest

GOOD = '{"summary": "A. B.", "tags": ["ai", "python", "llm"], "content_type": "article"}'


def test_valid_output_becomes_typed_object():
    digest = parse_digest(GOOD)
    assert isinstance(digest, SavedItemDigest)
    assert digest.tags == ["ai", "python", "llm"]


def test_invalid_json_gives_controlled_error():
    with pytest.raises(DigestParseError) as info:
        parse_digest("Sure! Here is the JSON: {summary")
    assert info.value.reason == "invalid_json"


def test_missing_tags_gives_controlled_error():
    with pytest.raises(DigestParseError) as info:
        parse_digest('{"summary": "A. B.", "content_type": "article"}')
    assert info.value.reason == "schema_error"
    assert "tags" in info.value.detail
