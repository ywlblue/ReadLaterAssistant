import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()                  # Read .env
client = OpenAI()              # Read OPENAI_API_KEY
article = sys.stdin.read()     # Read pasted article

response = client.responses.create(
    model=os.environ["OPENAI_MODEL"],
    instructions="Summarize the article in exactly 2 sentences.",
    input=article,
)
print(response.output_text)
