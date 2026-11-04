"""Retrieval-only evaluation on the development cases. No model call, no LLM judge.

Run from the repo root:
    python src/run_dev_eval.py
    python src/run_dev_eval.py --top-items 5 --chunk-k 30
    python src/run_dev_eval.py --split test --final-test   # Sprint 4 only

The final-test split is locked by default, so it cannot be used for tuning.
Both split files must match the sha256 in eval/dataset-manifest.json (frozen on 11/3).

Answerable cases  -> item-level Hit@5 and MRR (after removing duplicate items).
No-evidence cases -> abstained or not (top distance > MAX_DISTANCE, or no result).

Writes one JSON line per case to eval/results/<date>_dev_eval.jsonl
and prints a summary.
"""
import argparse
import hashlib
import json
import time
from datetime import date
from pathlib import Path

import chromadb

from answers import MAX_DISTANCE
from embeddings import embed_texts
from index import COLLECTION_NAME, retrieve

ROOT = Path(__file__).resolve().parent.parent
QUERIES_PATH = ROOT / "eval" / "dev.jsonl"
SPLIT_PATHS = {"dev": QUERIES_PATH, "test": ROOT / "eval" / "test.jsonl"}
MANIFEST_PATH = ROOT / "eval" / "dataset-manifest.json"
CHROMA_PATH = ROOT / "data" / "chroma"
RESULTS_DIR = ROOT / "eval" / "results"

TOP_ITEMS = 5   # score the first 5 distinct items
CHUNK_K = 30    # fetch more chunks than items, because one item can fill several chunk slots


def load_queries(path: Path = QUERIES_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def queries_path(split: str, final_test: bool = False) -> Path:
    if split == "test" and not final_test:
        raise SystemExit("The final-test split is locked during tuning. "
                         "Use --split test --final-test only for the Sprint 4 final run.")
    return SPLIT_PATHS[split]


def check_frozen(split: str, path: Path, manifest_path: Path = MANIFEST_PATH) -> None:
    # Like comparing a checksum before a release: if the cases changed, the old numbers are not comparable.
    expected = json.loads(manifest_path.read_text(encoding="utf-8"))["splits"][split]["sha256"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"{path.name} does not match {manifest_path.name} (frozen). "
                         "Do not edit frozen cases; add new ones as a new dataset version.")


def open_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_collection(COLLECTION_NAME)


def top_unique_items(chunks: list[dict], n: int) -> list[str]:
    # Keep order, drop repeats (like Java's LinkedHashSet), then take the first n.
    return list(dict.fromkeys(c["item_id"] for c in chunks))[:n]


# The later the expected item id appear in the retrieved list, the lower the rank
def reciprocal_rank(retrieved: list[str], expected: list[str]) -> float:
    for rank, item_id in enumerate(retrieved, 1):
        if item_id in expected:
            return 1 / rank
    return 0.0


def evaluate_one(row: dict, collection, top_items: int = TOP_ITEMS, chunk_k: int = CHUNK_K,
                 embed=embed_texts, max_distance=MAX_DISTANCE) -> dict:
    start = time.perf_counter()
    chunks = retrieve(row["query"], collection, chunk_k, embed=embed, **(row["filters"] or {}))
    latency_ms = (time.perf_counter() - start) * 1000

    retrieved = top_unique_items(chunks, top_items)
    top_distance = chunks[0]["distance"] if chunks else None
    abstained = top_distance is None or top_distance > max_distance

    result = {
        "id": row["id"],
        "query": row["query"],
        "type": row["type"],
        "filters": row["filters"],
        "answerable": row["answerable"],
        "expected_item_ids": row["expected_item_ids"],
        "retrieved_item_ids": retrieved,
        "top_distance": top_distance,
        "abstained": abstained,
        "latency_ms": latency_ms,
    }

    if row["answerable"]:
        expected = row["expected_item_ids"]
        rr = reciprocal_rank(retrieved, expected)
        result.update({
            "hit": rr > 0,
            "reciprocal_rank": rr,
            "first_hit_rank": round(1 / rr) if rr else None,
            "recall": len(set(expected) & set(retrieved)) / len(expected),
        })
        result["outcome"] = "Pass" if result["hit"] else "Failed"
    else:
        result["outcome"] = "Pass" if abstained else "Failed"

    return result


def summarize(results: list[dict], top_items: int = TOP_ITEMS) -> dict:
    answerable = [r for r in results if r["answerable"]]
    no_evidence = [r for r in results if not r["answerable"]]
    n = len(answerable)
    return {
        "answerable": n,
        f"hit@{top_items}": sum(r["hit"] for r in answerable) / n if n else None,
        "mrr": sum(r["reciprocal_rank"] for r in answerable) / n if n else None,
        # Answerable cases that would be refused at the retrieval layer.
        "answerable_abstained": sum(r["abstained"] for r in answerable),
        "no_evidence": len(no_evidence),
        "no_evidence_abstained": sum(r["abstained"] for r in no_evidence),
    }


def print_summary(results: list[dict], summary: dict, top_items: int, chunk_k: int, chunk_count: int) -> None:
    print(f"collection={COLLECTION_NAME} chunks={chunk_count} top_items={top_items} chunk_k={chunk_k}\n")
    for r in results:
        dist = f"{r['top_distance']:.3f}" if r["top_distance"] is not None else "-"
        if r["answerable"]:
            rank = r["first_hit_rank"] or "-"
            print(f"{r['id']} {r['outcome']:<6} rank={rank} dist={dist}  {r['query'][:60]}")
            if not r["hit"]:
                print(f"      expected  {r['expected_item_ids']}")
                print(f"      retrieved {r['retrieved_item_ids']}")
        else:
            print(f"{r['id']} {r['outcome']:<6} abstain dist={dist}  {r['query'][:60]}")

    s = summary
    print(f"\nanswerable {s['answerable']}: hit@{top_items}={s[f'hit@{top_items}']:.3f}  mrr={s['mrr']:.3f}  "
          f"(retrieval layer would refuse {s['answerable_abstained']})")
    print(f"no evidence {s['no_evidence']}: abstained {s['no_evidence_abstained']}/{s['no_evidence']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-items", type=int, default=TOP_ITEMS)
    parser.add_argument("--chunk-k", type=int, default=CHUNK_K)
    parser.add_argument("--split", choices=SPLIT_PATHS, default="dev")
    parser.add_argument("--final-test", action="store_true", help="unlock the final-test split (Sprint 4)")
    args = parser.parse_args()

    path = queries_path(args.split, args.final_test)
    check_frozen(args.split, path)

    collection = open_collection()
    chunk_count = collection.count()
    if chunk_count == 0:
        raise SystemExit(f"Collection {COLLECTION_NAME} is empty. Build the index first.")

    results = [evaluate_one(row, collection, args.top_items, args.chunk_k) for row in load_queries(path)]
    summary = summarize(results, args.top_items)
    print_summary(results, summary, args.top_items, args.chunk_k, chunk_count)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{date.today():%Y-%m-%d}_{args.split}_eval.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
