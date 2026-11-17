import os

from dotenv import load_dotenv
from openai import APITimeoutError, OpenAI, NOT_GIVEN

load_dotenv()

# Every LLM call is bounded. The SDK default is 600 s with 2 silent retries, which would
# outlast the bot's 120 s HTTP timeout. Worst cases: /review = 3 x 25 s, /ask = 2 x 25 s + embedding.
LLM_TIMEOUT_SECONDS = 25
LLM_MAX_RETRIES = 0


class LLMTimeOutException(Exception):
    pass


def reasoning_param():
    """Reasoning models (gpt-6-luna) accept reasoning.effort: none / low / medium / high.
    gpt-4o rejects the parameter, so nothing is sent when OPENAI_REASONING_EFFORT is unset."""
    effort = os.environ.get("OPENAI_REASONING_EFFORT")
    return {"effort": effort} if effort else NOT_GIVEN


def get_response(instructions: str, text: str, json_mode: bool = False, on_usage=None):
    """on_usage: optional callback, gets response.usage (input_tokens, output_tokens). Used by the Ask audit."""
    try:
        client = OpenAI(timeout=LLM_TIMEOUT_SECONDS, max_retries=LLM_MAX_RETRIES)
        response = client.responses.create(
            model=os.environ["OPENAI_MODEL"],
            instructions=instructions,
            input=text,
            reasoning=reasoning_param(),
            # Use NOT_GIVEN instead of None to avoid sending null
            text={"format": {"type": "json_object"}} if json_mode else NOT_GIVEN
        )
    except APITimeoutError as e:
        raise LLMTimeOutException(str(e)) from e
    if on_usage is not None and response.usage is not None:
        on_usage(response.usage)
    return response.output_text
