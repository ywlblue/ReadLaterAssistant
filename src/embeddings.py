from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

EMBEDDING_MODEL = "text-embedding-3-small"
# Bounded: worst case 2 x 15 s per call (the SDK default is 600 s with 2 retries).
EMBEDDING_TIMEOUT_SECONDS = 15
EMBEDDING_MAX_RETRIES = 1

load_dotenv()


def embed_texts(texts: list[str]) -> list[list[float]]:
    embedding = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        # By default, OpenAI process 1000 at once. To prevent token limit exceeds, send 100 in a batch.
        chunk_size=100,
        timeout=EMBEDDING_TIMEOUT_SECONDS,
        max_retries=EMBEDDING_MAX_RETRIES,
    )
    return embedding.embed_documents(texts)


if __name__ == '__main__':
    vectors = embed_texts(["hello", "JPA transaction", "Chroma where filter"])
    print(len(vectors), len(vectors[0]))
