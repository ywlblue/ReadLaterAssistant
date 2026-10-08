import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

ContentType = Literal["article", "tutorial", "news", "paper", "other"]


class SavedItemDigest(BaseModel):
    summary: str = Field(min_length=1)
    tags: list[str] = Field(min_length=3, max_length=5)
    content_type: ContentType


class DigestParseError(Exception):
    def __init__(self, reason, detail, raw_output):
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail
        self.raw_output = raw_output


def parse_digest(raw_output):
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise DigestParseError("invalid_json", str(e), raw_output) from e
    try:
        return SavedItemDigest.model_validate(data)
    except ValidationError as e:
        problems = "; ".join(f"{err['loc']}: {err['msg']}" for err in e.errors())
        raise DigestParseError("schema_error", problems, raw_output) from e
