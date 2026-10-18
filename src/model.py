import os

from dotenv import load_dotenv
from openai import APITimeoutError, OpenAI, NOT_GIVEN

load_dotenv()


class LLMTimeOutException(Exception):
    pass


def get_response(instructions: str, text: str, json_mode: bool = False):
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
    return response.output_text
