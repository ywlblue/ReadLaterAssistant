from typing import get_args

from schemas import ContentType

CONTENT_TYPES = list(get_args(ContentType))

SUMMARY_TEMPLATE = "Summarize the article in exactly {num_sentences} sentences."

DIGEST_TEMPLATE = """Return ONLY a JSON object. No markdown, no extra text.
Keys:
- "summary": string, exactly 2 sentences
- "tags": array of {min_tags} to {max_tags} short lowercase strings
- "content_type": one of {content_types}
Example: {{"summary": "...", "tags": ["tag1", "tag2", "tag3"], "content_type": "other"}}"""


def summary_prompt(num_sentences=2):
    return SUMMARY_TEMPLATE.format(num_sentences=num_sentences)


def digest_prompt(min_tags=3, max_tags=5):
    return DIGEST_TEMPLATE.format(
        min_tags=min_tags, max_tags=max_tags, content_types=", ".join(CONTENT_TYPES)
    )
