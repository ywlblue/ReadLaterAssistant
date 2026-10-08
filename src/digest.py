import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from prompts import summary_prompt, digest_prompt
from schemas import parse_digest, DigestParseError

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
raw = run(digest_prompt(), article)
try:
    digest = parse_digest(raw)
    print(digest.summary)
    print(digest.tags)
    print(digest.content_type)
except DigestParseError as e:
    print(f"DIGEST FAILED ({e.reason}): {e.detail}")
    print("--- raw output ---")
    print(e.raw_output)
    sys.exit(1)
