import os
import sys

from dotenv import load_dotenv
from langchain.schema.runnable import RunnableParallel
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

CONTENT_TYPES = ["article", "tutorial", "news", "paper", "other"]

SUMMARY_TEMPLATE = ("Summarize the following article in exactly {num_sentences} sentences.\n"
                    "Article: {article}")

DIGEST_TEMPLATE = """Given the article, do the following.
Article: {article}\n
Requirement: Return ONLY a JSON object. No markdown, no extra text.
Keys:
- "summary": string, exactly {num_sentences} sentences
- "tags": array of {min_tags} to {max_tags} short lowercase strings
- "content_type": one of {content_types}
Example: {{"summary": "...", "tags": ["tag1", "tag2", "tag3"], "content_type": "other"}}"""

load_dotenv()

summary_template = PromptTemplate(template=SUMMARY_TEMPLATE,
                                  input_variables=["article", "num_sentences"])

digest_template = PromptTemplate(template=DIGEST_TEMPLATE,
                                 input_variables=["article", "num_sentences", "min_tags", "max_tags", "content_types"])

llm = ChatOpenAI(model=os.environ["OPENAI_MODEL"])
# Strip the returned AIMessage from llm and get the text only
parser = StrOutputParser()

chain = RunnableParallel({
    "summary": summary_template | llm | parser,
    "digest": digest_template | llm | parser
    })

article = sys.stdin.read()
result = chain.invoke({"article": article, "num_sentences": 2, "min_tags": 3, "max_tags": 5,
                       "content_types": ", ".join(CONTENT_TYPES)})

print("=== SUMMARY ===")
print(result["summary"])
print("=== DIGEST ===")
print(result["digest"])
