import os

from dotenv import load_dotenv
from openai import APITimeoutError, OpenAI, NOT_GIVEN

load_dotenv()


class LLMTimeOutException(Exception):
    pass


def get_response(instructions: str, text: str, json_mode: bool = False, on_usage=None):
    """on_usage: optional callback, gets response.usage (input_tokens, output_tokens). Used by the Ask audit."""
    try:
        client = OpenAI()
        response = client.responses.create(
            model=os.environ["OPENAI_MODEL"],
            instructions=instructions,
            input=text,
            # Use NOT_GIVEN instead of None to avoid sending null
            text={"format": {"type": "json_object"}} if json_mode else NOT_GIVEN
        )
    except APITimeoutError as e:
        raise LLMTimeOutException(str(e)) from e
    if on_usage is not None and response.usage is not None:
        on_usage(response.usage)
    return response.output_text
