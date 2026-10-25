"""Replay the labeled Find queries against the Chroma index and record a baseline.

Run from anywhere:
    python src/run_find_eval.py            # top-5
    python src/run_find_eval.py --k 10

Writes one JSON line per query to eval/results/<date>_find_baseline_k<k>.jsonl
and prints a summary table.
"""
import argparse
import json
from datetime import date
from pathlib import Path

import chromadb

from embeddings import embed_texts
from index import COLLECTION_NAME, retrieve

ROOT = Path(__file__).resolve().parent.parent
QUERIES_PATH = ROOT / "eval" / "find_queries.jsonl"
CHROMA_PATH = ROOT / "data" / "chroma"
RESULTS_DIR = ROOT / "eval" / "results"


def load_queries(path: Path = QUERIES_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def open_collection():
    # Not set_up_chroma(): its path is relative, and get_or_create would silently
    # make an empty collection when run from the wrong folder.
    # get_collection raises if the index is missing, so we fail loudly instead.
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_collection(COLLECTION_NAME)


def unique_item_ids(chunks: list[dict]) -> list[str]:
    # Several chunks can come from the same item; keep the first (best) rank.
    seen = []
    for chunk in chunks:
        if chunk["item_id"] not in seen:
            seen.append(chunk["item_id"])
    return seen


def out_of_filter(chunks: list[dict], filters: dict) -> list[str]:
    """Chunk IDs that break the filter. Should always be empty."""
    bad = []
    for c in chunks:
        if filters.get("domain") and c["domain"] != filters["domain"]:
            bad.append(c["chunk_id"])
        elif filters.get("since") is not None and c["saved_day"] < filters["since"]:
            bad.append(c["chunk_id"])
        elif filters.get("until") is not None and c["saved_day"] > filters["until"]:
            bad.append(c["chunk_id"])
    return bad


def evaluate_one(row: dict, collection, k: int, embed=embed_texts) -> dict:
    filters = row.get("filters") or {}
    chunks = retrieve(row["query"], collection, k, embed=embed, **filters)

    retrieved = unique_item_ids(chunks)
    expected = row["expected_item_ids"]
    found = [i for i in expected if i in retrieved]
    ranks = [retrieved.index(i) + 1 for i in found]

    return {
        "query": row["query"],
        "filters": row.get("filters"),
        "expected_item_ids": expected,
        "retrieved_item_ids": retrieved,
        "hit": bool(found),
        "recall": round(len(found) / len(expected), 2),
        "first_hit_rank": min(ranks) if ranks else None,
        "out_of_filter_chunk_ids": out_of_filter(chunks, filters),
        "top_chunks": [
            {"chunk_id": c["chunk_id"], "item_id": c["item_id"],
             "distance": round(c["distance"], 4), "text": c["text"][:120]}
            for c in chunks
        ],
    }


def run(queries: list[dict], collection, k: int, embed=embed_texts) -> list[dict]:
    return [evaluate_one(row, collection, k, embed) for row in queries]


def print_summary(results: list[dict], k: int, chunk_count: int) -> None:
    print(f"collection={COLLECTION_NAME} chunks={chunk_count} k={k}\n")
    for n, r in enumerate(results, 1):
        mark = "HIT " if r["hit"] else "MISS"
        rank = r["first_hit_rank"] or "-"
        print(f"{n:>2}. {mark} rank={rank} recall={r['recall']:.2f}  {r['query'][:60]}")
        if not r["hit"]:
            print(f"      expected  {r['expected_item_ids']}")
            print(f"      retrieved {r['retrieved_item_ids']}")
        if r["out_of_filter_chunk_ids"]:
            print(f"      !! OUT OF FILTER: {r['out_of_filter_chunk_ids']}")

    hits = sum(r["hit"] for r in results)
    leaks = sum(len(r["out_of_filter_chunk_ids"]) for r in results)
    print(f"\nhit@{k}: {hits}/{len(results)}   out-of-filter chunks: {leaks}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    collection = open_collection()
    chunk_count = collection.count()
    if chunk_count == 0:
        raise SystemExit(f"Collection {COLLECTION_NAME} is empty. Build the index first.")

    results = run(load_queries(), collection, args.k)
    print_summary(results, args.k, chunk_count)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{date.today():%Y-%m-%d}_find_baseline_k{args.k}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
