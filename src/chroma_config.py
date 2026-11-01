from pathlib import Path

import chromadb

from index import COLLECTION_NAME

ROOT = Path(__file__).resolve().parent.parent
QUERIES_PATH = ROOT / "eval" / "baseline.jsonl"
CHROMA_PATH = ROOT / "data" / "chroma"


def setup_chroma():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_collection(COLLECTION_NAME)
