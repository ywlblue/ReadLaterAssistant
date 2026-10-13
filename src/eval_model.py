"""Run the digest prompt on fixed saved snapshots and record the results.

Usage: python src/eval_model.py            # 5 items, model from .env
       python src/eval_model.py --limit 3  # fewer items
"""
import argparse
import json
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

from prompts import digest_prompt
from schemas import DigestParseError, parse_digest
from storage import connect

# USD per 1M tokens. Estimates only: check https://openai.com/api/pricing/
# and override in .env with PRICE_INPUT_PER_M / PRICE_OUTPUT_PER_M.
DEFAULT_PRICES = {
    "gpt-4o": (2.50, 10.00),
}


def get_prices(model):
    default_in, default_out = DEFAULT_PRICES.get(model, (None, None))
    price_in = os.environ.get("PRICE_INPUT_PER_M", default_in)
    price_out = os.environ.get("PRICE_OUTPUT_PER_M", default_out)
    if price_in is None or price_out is None:
        return None, None
    return float(price_in), float(price_out)


def load_snapshots(conn, limit):
    # Oldest fetched items first, so the same 5 come back every run.
    return conn.execute(
        "SELECT id, url, title, content_text FROM saved_items "
        "WHERE status = 'fetched' ORDER BY saved_at, id LIMIT ?",
        (limit,),
    ).fetchall()


def run_one(client, model, item, price_in, price_out):
    result = {"item_id": item["id"], "url": item["url"], "chars": len(item["content_text"])}
    start = time.perf_counter()
    try:
        response = client.responses.create(
            model=model, instructions=digest_prompt(),
            input=f"Article:\n{item['content_text']}\n\nReturn the digest as JSON.",
            text={"format": {"type": "json_object"}},
        )
    except Exception as e:  # timeout, rate limit, bad model name...
        result.update(ok=False, error=f"api_error: {type(e).__name__}: {e}",
                      latency_s=round(time.perf_counter() - start, 2))
        return result

    result["latency_s"] = round(time.perf_counter() - start, 2)
    result["input_tokens"] = response.usage.input_tokens
    result["output_tokens"] = response.usage.output_tokens
    if price_in is not None:
        cost = (result["input_tokens"] * price_in + result["output_tokens"] * price_out) / 1_000_000
        result["cost_usd"] = round(cost, 6)

    try:
        digest = parse_digest(response.output_text)
        result.update(ok=True, summary=digest.summary, tags=digest.tags,
                      content_type=digest.content_type)
    except DigestParseError as e:
        result.update(ok=False, error=f"{e.reason}: {e.detail}", raw_output=e.raw_output)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    load_dotenv()
    model = os.environ["OPENAI_MODEL"]
    price_in, price_out = get_prices(model)
    conn = connect(os.environ.get("READLATER_DB", "data/readlater.db"))
    items = load_snapshots(conn, args.limit)
    if len(items) < args.limit:
        print(f"Only {len(items)} fetched items. Save more with src/save.py first.")
        return

    client = OpenAI(timeout=60)
    results = []
    for item in items:
        r = run_one(client, model, item, price_in, price_out)
        print(f"{'OK  ' if r['ok'] else 'FAIL'} {r['latency_s']:>5}s  {r['url']}"
              + ("" if r["ok"] else f"  -> {r['error']}"))
        results.append(r)

    ok = [r for r in results if r["ok"]]
    costs = [r["cost_usd"] for r in results if "cost_usd" in r]
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "config": {"model": model,
                   "prompt": "digest_prompt(min_tags=3, max_tags=5) + "
                             "'Return the digest as JSON.' in input + json_object mode",
                   "instructions_text": digest_prompt(),
                   "price_input_per_m": price_in, "price_output_per_m": price_out},
        "totals": {
            "items": len(results),
            "valid": len(ok),
            "avg_latency_s": round(sum(r["latency_s"] for r in results) / len(results), 2),
            "total_cost_usd": round(sum(costs), 6) if costs else None,
        },
        "items": results,
    }

    os.makedirs("eval/results", exist_ok=True)
    path = f"eval/results/{datetime.now().strftime('%Y-%m-%d')}_{model}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nvalid {len(ok)}/{len(results)}, avg {report['totals']['avg_latency_s']}s, "
          f"cost ${report['totals']['total_cost_usd']}")
    print("saved:", path)


if __name__ == "__main__":
    main()
