import pytest

from digest import digest
from model import LLMTimeOutException
from schemas import DigestParseError


def test_digest_get_not_json_response():
    with pytest.raises(DigestParseError):
        digest("This is an article", call_model=lambda x, y: "not json")


def test_digest_get_timeout_exception():
    def raise_error_method(x, y):
        raise LLMTimeOutException("Timeout")

    with pytest.raises(LLMTimeOutException):
        digest("This is an article", call_model=raise_error_method)


