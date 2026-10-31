import json
import time
from datetime import date
from pathlib import Path

import chromadb

from answers import answer, MAX_DISTANCE
from embeddings import embed_texts
from index import COLLECTION_NAME
from model import get_response

ROOT = Path(__file__).resolve().parent.parent
QUERIES_PATH = ROOT / "eval" / "baseline.jsonl"
CHROMA_PATH = ROOT / "data" / "chroma"
RESULTS_DIR = ROOT / "eval" / "results"


def load_queries(path: Path = QUERIES_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def open_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_collection(COLLECTION_NAME)


def evaluate_one(row: dict, collection, k: int = 5, embed=embed_texts, call_model=get_response, max_distance=MAX_DISTANCE) -> dict:
    start = time.perf_counter()
    result = answer(query=row["query"], collection=collection, k=k, embed=embed,
                    call_model=call_model, max_distance=max_distance, **(row["filters"] or {}))
    latency_ms = (time.perf_counter() - start) * 1000

    cited = list(dict.fromkeys(s.item_id for s in result.sources))
    citation_found = set(row["expected_item_ids"]) <= set(cited)
    passages = [
        "".join(passage.split())
        for passage in (row.get("supporting_passage") or [])
    ]

    excerpts = [
        "".join(source.excerpt.split())
        for source in result.sources
    ]

    passage_found = (
        any(
            passage in excerpt
            for passage in passages
            for excerpt in excerpts
            if passage
        )
        if passages else None
    )

    if row["answerable"]:
        ok = citation_found and not result.insufficient_evidence and passage_found
        if not citation_found:
            reason = "citation_not_found"
        elif not passage_found:
            reason = "passage_not_found"
        else:
            reason = None
    else:
        ok = result.insufficient_evidence
        reason = None if ok else "not_abstained"

    return {
        "id": row["id"],
        "query": row["query"],
        "type": row["type"],
        "outcome": "Pass" if ok else "Failed",
        "latency_ms": latency_ms,
        "top_distance": result.top_distance,
        "retrieved_item_ids": cited,
        "chunk_ids": [source.chunk_id for source in result.sources],
        "answer": result.answer,
        "excerpt": [source.excerpt for source in result.sources],
        "layer": result.layer if result.layer else "answer",
        "passage_found": passage_found,
        "reason": reason
    }


def main():
    queries = load_queries()
    clt = open_collection()
    results = []
    for query in queries:
        results.append(evaluate_one(query, clt))

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{date.today():%Y-%m-%d}_baseline.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"saved {out.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
