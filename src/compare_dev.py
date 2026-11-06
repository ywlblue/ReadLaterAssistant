"""Build eval/dev-comparison.csv from per-method dev result files. No search, no model call.

Run from the repo root (after run_dev_eval.py for each method):
    python src/compare_dev.py                    # newest dense + lexical files
    python src/compare_dev.py --date 2026-11-05  # files from one day

One row per search method: Hit@5, MRR, no-evidence abstention, mean latency,
plus the git commit from the matching .run.json. A last row counts how many
dev cases got the exact same top-5 items from every method.
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "eval" / "results"
OUT_PATH = ROOT / "eval" / "dev-comparison.csv"
METHODS = ["dense", "lexical"]

FIELDS = ["method", "cases", "answerable", "hit@5", "mrr", "answerable_abstained",
          "no_evidence", "no_evidence_abstained", "mean_latency_ms", "git_commit", "source_file"]


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def result_file(method: str, day: str | None) -> Path:
    # File names start with the date, so sorting by name = sorting by date (newest last).
    pattern = f"{day or '*'}_dev_{method}_eval.jsonl"
    files = sorted(RESULTS_DIR.glob(pattern))
    if not files:
        raise SystemExit(f"No result file matches {pattern}. Run: python src/run_dev_eval.py --search {method}")
    return files[-1]


def method_row(method: str, rows: list[dict]) -> dict:
    answerable = [r for r in rows if r["answerable"]]
    no_evidence = [r for r in rows if not r["answerable"]]
    n = len(answerable)
    return {
        "method": method,
        "cases": len(rows),
        "answerable": n,
        "hit@5": round(sum(r["hit"] for r in answerable) / n, 3) if n else None,
        "mrr": round(sum(r["reciprocal_rank"] for r in answerable) / n, 3) if n else None,
        "answerable_abstained": sum(r["abstained"] for r in answerable),
        "no_evidence": len(no_evidence),
        "no_evidence_abstained": sum(r["abstained"] for r in no_evidence),
        "mean_latency_ms": round(sum(r["latency_ms"] for r in rows) / len(rows), 1) if rows else None,
    }


def same_top5_count(rows_by_method: dict[str, list[dict]]) -> tuple[int, int]:
    # For each case id, collect the top-5 list from every method; "same" = all lists equal.
    by_id: dict[str, list] = {}
    for rows in rows_by_method.values():
        for r in rows:
            by_id.setdefault(r["id"], []).append(r["retrieved_item_ids"])
    same = sum(1 for lists in by_id.values() if all(x == lists[0] for x in lists))
    return same, len(by_id)


def git_commit_of(path: Path) -> str:
    run_path = path.with_name(path.stem + ".run.json")
    if not run_path.exists():
        return "unknown"  # older runs (before 11/5) have no .run.json
    return json.loads(run_path.read_text(encoding="utf-8"))["git_commit"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="use result files from this day, e.g. 2026-11-05 (default: newest)")
    args = parser.parse_args()

    rows_by_method, table = {}, []
    for method in METHODS:
        path = result_file(method, args.date)
        rows = load_jsonl(path)
        rows_by_method[method] = rows
        table.append({**method_row(method, rows), "git_commit": git_commit_of(path),
                      "source_file": path.relative_to(ROOT).as_posix()})

    case_sets = {m: {r["id"] for r in rows} for m, rows in rows_by_method.items()}
    if len({frozenset(s) for s in case_sets.values()}) != 1:
        raise SystemExit("Methods were run on different cases; results are not comparable.")

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(table)

    for row in table:
        print(f"{row['method']:<8} hit@5={row['hit@5']} mrr={row['mrr']} "
              f"no-evidence abstained {row['no_evidence_abstained']}/{row['no_evidence']} "
              f"latency {row['mean_latency_ms']} ms  ({row['git_commit']})")
    same, total = same_top5_count(rows_by_method)
    print(f"identical top-5 across methods: {same}/{total}")
    print(f"saved {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
