import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from prompts import summary_prompt, digest_prompt

load_dotenv()
client = OpenAI()


def run(instructions, input_article):
    response = client.responses.create(
        model=os.environ["OPENAI_MODEL"],
        instructions=instructions,
        input=input_article,
    )
    return response.output_text


article = sys.stdin.read()
print("=== ARTICLE ===")
print(article)
print("=== SUMMARY ===")
print(run(summary_prompt(), article))
print("=== DIGEST ===")
print(run(digest_prompt(), article))
