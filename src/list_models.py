from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
for m in OpenAI().models.list():
    print(m.id)