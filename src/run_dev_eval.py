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
import subprocess
import time
from datetime import date
from pathlib import Path

import chromadb

from answers import MAX_DISTANCE
from build_fts import fts_chunk_count, lexical_search
from hybrid_search import make_hybrid_search, RRF_K
from index import COLLECTION_NAME, make_dense_search

ROOT = Path(__file__).resolve().parent.parent
QUERIES_PATH = ROOT / "eval" / "dev.jsonl"
SPLIT_PATHS = {"dev": QUERIES_PATH, "test": ROOT / "eval" / "test.jsonl"}
MANIFEST_PATH = ROOT / "eval" / "dataset-manifest.json"
CHROMA_PATH = ROOT / "data" / "chroma"
RESULTS_DIR = ROOT / "eval" / "results"

TOP_ITEMS = 5  # score the first 5 distinct items
CHUNK_K = 30  # fetch more chunks than items, because one item can fill several chunk slots


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


def git_commit() -> str:
    run = lambda *cmd: subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout.strip()
    commit = run("git", "rev-parse", "--short", "HEAD") or "unknown"
    dirty = run("git", "status", "--porcelain", "--", ".", ":!eval/results")
    return commit + ("-dirty" if dirty else "")


def open_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_collection(COLLECTION_NAME)


def top_unique_items(chunks: list[dict], n: int) -> list[str]:
    # Keep order, drop repeats, then take the first n.
    return list(dict.fromkeys(c["item_id"] for c in chunks))[:n]


# The later the expected item id appear in the retrieved list, the lower the rank
def reciprocal_rank(retrieved: list[str], expected: list[str]) -> float:
    for rank, item_id in enumerate(retrieved, 1):
        if item_id in expected:
            return 1 / rank
    return 0.0


def evaluate_one(row: dict, search, abstain, top_items: int = TOP_ITEMS, chunk_k: int = CHUNK_K,
                 search_method='dense') -> dict:
    start = time.perf_counter()
    chunks = search(row["query"], chunk_k, **(row["filters"] or {}))
    latency_ms = (time.perf_counter() - start) * 1000

    retrieved = top_unique_items(chunks, top_items)
    top_distance = chunks[0].get("distance") if chunks else None  # lexical doesn't have distance → None
    abstained = abstain(chunks)

    result = {
        "id": row["id"],
        "query": row["query"],
        "type": row["type"],
        "search_method": search_method,
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


def dense_abstain(max_distance=MAX_DISTANCE):
    return lambda chunks: (not chunks
                           or chunks[0].get("distance") is None
                           or chunks[0]["distance"] > max_distance)


def lexical_abstain(chunks):
    return not chunks


def validate_fts_count(expected_chunk_count: int):
    fts_count = fts_chunk_count()
    if fts_count != expected_chunk_count:
        raise SystemExit(f"chunks_fts has {fts_count} chunks but Chroma has {expected_chunk_count}. "
                         "Run build_fts.py so both use the same corpus.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-items", type=int, default=TOP_ITEMS)
    parser.add_argument("--chunk-k", type=int, default=CHUNK_K)
    parser.add_argument("--split", choices=SPLIT_PATHS, default="dev")
    parser.add_argument("--final-test", action="store_true", help="unlock the final-test split (Sprint 4)")
    parser.add_argument("--search", choices=["dense", "lexical", "hybrid"], default="dense")
    args = parser.parse_args()

    path = queries_path(args.split, args.final_test)
    check_frozen(args.split, path)

    collection = open_collection()
    chunk_count = collection.count()
    if chunk_count == 0:
        raise SystemExit(f"Collection {COLLECTION_NAME} is empty. Build the index first.")

    search_method = args.search

    if search_method == "dense":
        search = make_dense_search(collection)
        abstain = dense_abstain(MAX_DISTANCE)
    elif search_method == "lexical":
        validate_fts_count(chunk_count)
        search = lexical_search
        abstain = lexical_abstain
    else:
        validate_fts_count(chunk_count)
        search = make_hybrid_search(collection)
        abstain = dense_abstain(MAX_DISTANCE)

    commit = git_commit()
    run_start = time.perf_counter()
    results = [evaluate_one(row, search=search, abstain=abstain, top_items=args.top_items, chunk_k=args.chunk_k,
                            search_method=search_method)
               for row in load_queries(path)]
    summary = summarize(results, args.top_items)
    print_summary(results, summary, args.top_items, args.chunk_k, chunk_count)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{date.today():%Y-%m-%d}_{args.split}_{search_method}_eval.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"saved {out.relative_to(ROOT)}")

    elapsed_s = time.perf_counter() - run_start
    queries = load_queries(path)

    uses_dense = search_method in ("dense", "hybrid")
    # Only dense and hybrid search will call embedding api
    est_tokens = sum(len(q["query"]) // 4 + 1 for q in queries) if uses_dense else 0
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    run_record = {
        "date": f"{date.today():%Y-%m-%d}",
        "git_commit": commit,
        "config": {
            "split": args.split,
            "search": search_method,
            "top_items": args.top_items,
            "chunk_k": args.chunk_k,
            "max_distance": MAX_DISTANCE if uses_dense else None,
            "embedding_model": "text-embedding-3-small" if uses_dense else None,
            "rrf_k": RRF_K if search_method == 'hybrid' else None,
        },
        "corpus": {**manifest["corpus"], "chunks_now": chunk_count},
        "dataset_sha256": manifest["splits"][args.split]["sha256"],
        "elapsed_s": round(elapsed_s, 2),
        "est_tokens": est_tokens,
        "est_cost_usd": round(est_tokens * 0.02 / 1_000_000, 6),  # text-embedding-3-small: $0.02 / 1M tokens
        "summary": summary,
    }
    run_path = out.with_name(out.stem + ".run.json")
    run_path.write_text(json.dumps(run_record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"saved {run_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
