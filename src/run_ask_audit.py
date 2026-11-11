"""Run Ask on 10 fixed development cases and write a sheet for a manual answer/citation audit.

Run from the repo root:
    python src/run_ask_audit.py

Uses the production Ask path (answers.answer: dense retrieval, k=5, MAX_DISTANCE, gpt model from .env).
Development split only; the final-test split is never read here.

Writes:
    eval/results/<date>_dev_ask_audit.jsonl   one JSON line per case (machine-readable, human fields = null)
    eval/results/<date>_dev_ask_audit.md      the sheet you fill in by hand
After filling the .md, copy the yes/no/partial values into the .jsonl (or ask Claude to).
"""
import json
import os
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from answers import answer
from model import get_response
from run_dev_eval import QUERIES_PATH, RESULTS_DIR, ROOT, check_frozen, load_queries, open_collection

load_dotenv()

# Fixed choice so the audit is repeatable. Mix of types, all answerable:
# 5 ask (q06-q10), 2 filter (q11 domain, q14 date), 2 vague (q01, q29 close to the 0.6 threshold),
# 1 multi-passage find (q23, 3 gold items).
AUDIT_IDS = ["q06", "q07", "q08", "q09", "q10", "q11", "q14", "q01", "q29", "q23"]

# USD per 1M tokens. Check the OpenAI pricing page if the model changes.
PRICES = {"gpt-4o": {"input": 2.50, "output": 10.00}}


def audit_one(row: dict, collection) -> dict:
    usage = {"input_tokens": 0, "output_tokens": 0, "model_calls": 0}

    def on_usage(u):
        usage["input_tokens"] += u.input_tokens
        usage["output_tokens"] += u.output_tokens
        usage["model_calls"] += 1

    call_model = lambda instructions, text, json_mode=False: get_response(instructions, text, json_mode, on_usage)

    start = time.perf_counter()
    result = answer(row["query"], collection, call_model=call_model, **(row["filters"] or {}))
    latency_ms = (time.perf_counter() - start) * 1000

    cited_items = list(dict.fromkeys(s.item_id for s in result.sources))
    return {
        "id": row["id"],
        "type": row["type"],
        "query": row["query"],
        "filters": row["filters"],
        "expected_item_ids": row["expected_item_ids"],
        "supporting_passage": row.get("supporting_passage"),
        "answer": result.answer,
        "insufficient_evidence": result.insufficient_evidence,
        "layer": result.layer,
        "top_distance": result.top_distance,
        "sources": [{"ref": s.ref, "item_id": s.item_id, "url": s.url, "chunk_id": s.chunk_id,
                     "excerpt": s.excerpt} for s in result.sources],
        # Machine check only: did it cite at least one gold item? Not the same as "the citation supports the answer".
        "cites_gold_item": bool(set(cited_items) & set(row["expected_item_ids"])),
        "latency_ms": round(latency_ms, 1),
        **usage,
        # Filled in by hand from the .md sheet.
        "human_relevant": None,            # yes / no / partial: does the answer address the question?
        "human_citation_supported": None,  # yes / no / partial: do the cited excerpts actually say this?
        "human_notes": None,
    }


def cost_usd(rows: list[dict], model: str) -> float | None:
    price = PRICES.get(model)
    if price is None:
        return None
    total_in = sum(r["input_tokens"] for r in rows)
    total_out = sum(r["output_tokens"] for r in rows)
    return round((total_in * price["input"] + total_out * price["output"]) / 1_000_000, 4)


def write_sheet(path: Path, rows: list[dict], model: str) -> None:
    lines = [f"# Ask audit {date.today():%Y-%m-%d} (dev, model={model})", "",
             "Fill each case: relevant = yes/no/partial, citation_supported = yes/no/partial.", "",
             "Rubric:",
             "- relevant: yes = answers the question; partial = on topic but incomplete; no = off topic or wrong.",
             "- citation_supported: yes = every claim is in a cited excerpt; partial = some claims are not;"
             " no = excerpts do not support the answer.", ""]
    for r in rows:
        lines += [f"## {r['id']} ({r['type']}) {r['latency_ms']:.0f} ms, "
                  f"{r['input_tokens']}+{r['output_tokens']} tokens, top_distance={r['top_distance']}",
                  "", f"**Q:** {r['query']}  ", f"**Filters:** {r['filters']}  ",
                  f"**Expected items:** {r['expected_item_ids']}  ",
                  f"**Cites a gold item (machine):** {r['cites_gold_item']}", "",
                  f"**Answer:** {r['answer']}", ""]
        for s in r["sources"]:
            excerpt = s["excerpt"].replace("\n", " ")
            # Full excerpt: the model saw the whole chunk, so the auditor must too (11/10: [:600] hid the evidence).
            lines.append(f"- [{s['ref']}] `{s['item_id']}` {s['url']}  \n  > {excerpt}")
        lines += ["", "- relevant: ", "- citation_supported: ", "- notes: ", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    check_frozen("dev", QUERIES_PATH)
    by_id = {r["id"]: r for r in load_queries(QUERIES_PATH)}
    collection = open_collection()
    model = os.environ.get("OPENAI_MODEL", "unknown")

    rows = []
    for case_id in AUDIT_IDS:
        r = audit_one(by_id[case_id], collection)
        print(f"{r['id']} {r['latency_ms']:>7.0f} ms  tokens {r['input_tokens']}+{r['output_tokens']}  "
              f"gold cited={r['cites_gold_item']}  abstained={r['insufficient_evidence']}")
        rows.append(r)

    stem = f"{date.today():%Y-%m-%d}_dev_ask_audit"
    jsonl = RESULTS_DIR / f"{stem}.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    md = RESULTS_DIR / f"{stem}.md"
    write_sheet(md, rows, model)

    latencies = sorted(r["latency_ms"] for r in rows)
    print(f"\nmodel={model}  mean latency {sum(latencies) / len(latencies):.0f} ms  "
          f"max {latencies[-1]:.0f} ms  est cost ${cost_usd(rows, model)} for {len(rows)} asks")
    print(f"saved {jsonl.relative_to(ROOT)}\nsaved {md.relative_to(ROOT)}  <- fill this in by hand")


if __name__ == "__main__":
    main()
