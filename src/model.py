import os

from dotenv import load_dotenv
from openai import APITimeoutError, OpenAI

load_dotenv()


class LLMTimeOutException(Exception):
    pass


def get_response(instructions: str, text: str):
    try:
        client = OpenAI()
        response = client.responses.create(
            model=os.environ["OPENAI_MODEL"],
            instructions=instructions,
            input=text,
        )
    except APITimeoutError as e:
        raise LLMTimeOutException(str(e)) from e
    return response.output_text
