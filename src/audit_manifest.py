"""Audit the frozen eval dataset. Read-only: no search, no scoring.

Checks that dataset-manifest.json matches dev.jsonl / test.jsonl,
and that every gold item and supporting passage exists in SQLite.

Run: python src/audit_manifest.py
"""
import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

MANIFEST = Path("eval/dataset-manifest.json")
DB = "data/readlater.db"

problems = []


def check(ok, msg):
    if not ok:
        problems.append(msg)


def load_cases(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def no_space(text):
    return re.sub(r"\s+", "", text or "")


def audit_split(name, info, conn):
    path = Path(info["file"])
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    check(sha == info["sha256"], f"{name}: sha256 changed, file was edited after freeze")

    cases = load_cases(path)
    answerable = [c for c in cases if c["answerable"]]
    no_ev = [c for c in cases if not c["answerable"]]

    # 1. Counts in the manifest match the real file
    check(len(cases) == info["cases"], f"{name}: {len(cases)} cases, manifest says {info['cases']}")
    check(len(answerable) == info["answerable"], f"{name}: {len(answerable)} answerable, manifest says {info['answerable']}")
    check(len(no_ev) == info["no_evidence"], f"{name}: {len(no_ev)} no_evidence, manifest says {info['no_evidence']}")
    types = Counter(c["type"] for c in cases)
    check(dict(types) == info["by_type"], f"{name}: by_type {dict(types)} != manifest {info['by_type']}")
    origins = Counter(c["origin"] for c in cases)
    check(dict(origins) == info["by_origin"], f"{name}: by_origin {dict(origins)} != manifest {info['by_origin']}")
    with_filters = sorted(c["id"] for c in cases if c["filters"])
    check(with_filters == sorted(info["with_filters"]), f"{name}: with_filters {with_filters} != manifest")

    ids = [c["id"] for c in cases]
    check(len(ids) == len(set(ids)), f"{name}: duplicate case ids")

    # 2. Each case is valid against the database
    for c in cases:
        cid = c["id"]
        if not c["answerable"]:
            check(not c["expected_item_ids"], f"{cid}: no_evidence case has expected_item_ids")
            continue
        check(c["expected_item_ids"], f"{cid}: answerable case has no expected_item_ids")
        passages = c["supporting_passage"] or []
        if cid in info["multi_passage"]:
            check(len(c["expected_item_ids"]) + len(passages) >= 2, f"{cid}: marked multi_passage but has only 1 item/passage")

        texts = []
        for item_id in c["expected_item_ids"]:
            row = conn.execute(
                "SELECT domain, content_text, CAST(strftime('%Y%m%d', saved_at) AS INTEGER) "
                "FROM saved_items WHERE id = ?", (item_id,)).fetchone()
            if row is None:
                problems.append(f"{cid}: gold item {item_id} not in saved_items")
                continue
            domain, text, saved_day = row
            texts.append(no_space(text))
            n_chunks = conn.execute("SELECT COUNT(*) FROM chunks WHERE item_id = ?", (item_id,)).fetchone()[0]
            check(n_chunks > 0, f"{cid}: gold item {item_id} has no chunks (not indexed)")

            f = c["filters"] or {}
            check(f.get("domain") in (None, domain), f"{cid}: item {item_id} domain {domain} != filter {f.get('domain')}")
            check(f.get("since") is None or saved_day >= f["since"], f"{cid}: item {item_id} saved {saved_day} < since {f.get('since')}")
            check(f.get("until") is None or saved_day <= f["until"], f"{cid}: item {item_id} saved {saved_day} > until {f.get('until')}")

        for p in passages:
            check(any(no_space(p) in t for t in texts), f"{cid}: passage not found in gold text: {p[:50]}...")

    return cases


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB)
    splits = manifest["splits"]

    dev = audit_split("dev", splits["dev"], conn)
    test = audit_split("test", splits["test"], conn)

    # 3. Totals and overall rules from the plan
    all_cases = dev + test
    n_ans = sum(c["answerable"] for c in all_cases)
    n_multi = len(splits["dev"]["multi_passage"]) + len(splits["test"]["multi_passage"])
    check(len(all_cases) == manifest["totals"]["cases"] == 50, f"total cases {len(all_cases)}, expected 50")
    check(n_ans == manifest["totals"]["answerable"] == 40, f"total answerable {n_ans}, expected 40")
    check(n_multi == manifest["totals"]["multi_passage"] and n_multi >= 5, f"multi_passage {n_multi}, need >= 5")
    check(any(c["type"] == "vague" for c in all_cases), "no vague-memory cases")
    check(any(c["filters"] for c in all_cases), "no filter cases")

    # 4. Same query must not appear in both dev and test
    overlap = {c["query"] for c in dev} & {c["query"] for c in test}
    check(not overlap, f"same query in dev and test: {overlap}")

    print(f"Checked {len(dev)} dev + {len(test)} test cases (no search, no scoring).")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(" -", p)
        raise SystemExit(1)
    print("OK: manifest matches files and database.")


if __name__ == "__main__":
    main()
