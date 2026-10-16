import logging
import sys

from logging_config import setup_logging
from model import get_response, LLMTimeOutException
from prompts import digest_prompt
from schemas import parse_digest, DigestParseError, SavedItemDigest

logger = logging.getLogger(__name__)


def digest(input_article: str, call_model=get_response) -> SavedItemDigest:
    try:
        raw_response = call_model(digest_prompt(), input_article)
        return parse_digest(raw_response)
    except LLMTimeOutException as timeout_err:
        logger.log(
            logging.ERROR,
            str(timeout_err))
        raise
    except DigestParseError as parsing_err:
        logger.log(
            logging.ERROR,
            f"DIGEST FAILED ({parsing_err.reason}): {parsing_err.detail}")
        raise


if __name__ == '__main__':
    setup_logging()
    article = sys.stdin.read()
    print("=== ARTICLE ===")
    print(article)
    print("=== DIGEST ===")
    result = digest(article)
    print(f"Summary: {result.summary}")
    print(f"Tags: {result.tags}")
    print(f"Content Type: {result.content_type}")
