import json
from datetime import date
from pathlib import Path

import chromadb

from answers import answer, MAX_DISTANCE
from embeddings import embed_texts
from index import COLLECTION_NAME
from model import get_response

ROOT = Path(__file__).resolve().parent.parent
QUERIES_PATH = ROOT / "eval" / "no_evidence.jsonl"
CHROMA_PATH = ROOT / "data" / "chroma"
RESULTS_DIR = ROOT / "eval" / "results"


def load_queries(path: Path = QUERIES_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def open_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_collection(COLLECTION_NAME)


def evaluate_one(row: dict, collection, k: int = 5, embed=embed_texts, call_model=get_response,
                 max_distance=MAX_DISTANCE) -> dict:
    result = answer(query=row["query"], collection=collection, k=k, embed=embed,
                    call_model=call_model, max_distance=max_distance)
    return {
        "query": row["query"],
        "top1_distance": result.top_distance,
        "insufficient_evidence": result.insufficient_evidence,
        "layer": result.layer,
        "answer": result.answer
    }


def main():
    queries = load_queries()
    clt = open_collection()
    results = []
    for query in queries:
        results.append(evaluate_one(query, clt))

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{date.today():%Y-%m-%d}_no_evidence_max_distance_{MAX_DISTANCE}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"saved {out.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
