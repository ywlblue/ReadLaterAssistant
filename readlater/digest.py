import logging
import sys

from readlater.logging_config import setup_logging
from readlater.model import get_response, LLMTimeOutException
from readlater.prompts import digest_prompt
from readlater.schemas import parse_digest, DigestParseError, SavedItemDigest

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2  # first call + one malformed-output retry


def digest(input_article: str, call_model=get_response) -> SavedItemDigest:
    """Malformed output (bad JSON / wrong schema) gets exactly one retry. Timeouts are not retried."""
    text = f"Article:\n{input_article}\n\nReturn the digest as JSON."
    try:
        for attempt in range(MAX_ATTEMPTS):
            raw_response = call_model(digest_prompt(), text, True)
            try:
                return parse_digest(raw_response)
            except DigestParseError as parsing_err:
                if attempt == MAX_ATTEMPTS - 1:
                    raise
                logger.warning("digest retry after %s", parsing_err.reason)
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
