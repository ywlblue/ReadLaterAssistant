"""Offline workflow evaluation (M3).

Each case in eval/workflow-cases.jsonl sends one or more chat messages through the
SAME path the Telegram bot uses:

    bot.dispatch(text) -> route() -> bot handler -> HTTP -> FastAPI endpoint -> storage / model

Nothing leaves the machine:
  - HTTP calls from the bot go to FastAPI's TestClient (no uvicorn needed)
  - SQLite is a temp file per case (db.DB_PATH is patched, so every connect() uses it)
  - Chroma is an in-memory collection per case, with a fake embedding
  - the LLM is a fake chosen by the case ("fake_model")
  - page fetching is a fake chosen by the case ("pages")

Run:  python src/eval_workflow.py            (all cases)
      python src/eval_workflow.py W03 W07    (only these ids)
Writes eval/workflow-results.json and exits 1 if any case fails.

---------------------------------------------------------------------------
Case format (one JSON object per line)
---------------------------------------------------------------------------
{
  "id": "W01",                      required, unique
  "category": "valid_command",      free text, used for the summary
  "description": "...",             one line, what this case proves
  "fake_model": "ok",               ok | error | timeout | bad_json | bad_then_ok | empty | bad_ref
  "embed": "ok",                    ok | timeout   (query embedding for /ask and /find)
  "api": "ok",                      ok | timeout | down   (the bot's HTTP call to the API)
  "setup": {                        all keys optional
    "items": [                      rows in saved_items, referenced later as {item:0}, {item:1} ...
      {"url": "https://a.com/x", "title": "X", "status": "digested",
       "summary": "...", "tags": ["a","b","c"], "days_ago": 3, "content": "..."}
    ],
    "opened": [0],                  item indexes already marked opened
    "recommended_days_ago": {"1": 2},  item index -> recommended N days ago
    "chunks": [{"item": 0, "distance": "near", "text": "..."}],   near | mid | far
    "pages": {"https://a.com/new": "ok"}   url -> ok | not_found | paywall | network
  },
  "steps": [                        messages, in order
    {"send": "/review",
     "expect_contains": ["Why:"],           every string must be in the reply
     "expect_not_contains": ["Encounter an error"]}
  ],
  "expect_db": {                    optional, checked after the last step
    "review_recommendations": 2,    row counts per table
    "item_opens": 1,
    "request_events": 2,
    "item_status": {"0": "digested"},  item index -> status
    "feedback": 1,                  request_events rows with feedback set
    "urls": {"https://a.com/new": {"status": "digest_failed", "has_content": true}}
  },
  "expect_model_calls": 1           optional, how many times the fake model was called
}

Placeholders inside "send": {item:N} -> item id, {last_request_id} -> the last
"Request ID: ..." seen in a reply.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

BASE_DIR = Path(__file__).resolve().parent.parent
CASES_PATH = BASE_DIR / "eval" / "workflow-cases.jsonl"
RESULTS_PATH = BASE_DIR / "eval" / "workflow-results.json"

# bot.py reads these at import time; the runner never talks to Telegram or OpenAI.
os.environ.setdefault("ACCEPT_BOT_FROM_ID", "0")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "offline")
os.environ.setdefault("OPENAI_MODEL", "offline")
os.environ.setdefault("OPENAI_API_KEY", "offline")

import chromadb  # noqa: E402

import chroma_config  # noqa: E402

# api.py builds its Chroma collection at import time. Swap it before importing api,
# so the runner never opens the real index (and works on a clean checkout).
_chroma = chromadb.EphemeralClient()


def _new_collection():
    return _chroma.create_collection(f"wf_{uuid.uuid4().hex}", metadata={"hnsw:space": "cosine"})


chroma_config.setup_chroma = _new_collection

import api  # noqa: E402
import bot  # noqa: E402
import db  # noqa: E402
from answers import answer as real_answer  # noqa: E402
from digest import digest as real_digest  # noqa: E402
from events import connect_events  # noqa: E402
from fetch import FetchResult  # noqa: E402
from model import LLMTimeOutException  # noqa: E402
from review import connect_review, review_reason as real_review_reason  # noqa: E402
from schemas import SavedItemDigest  # noqa: E402
from storage import connect  # noqa: E402
from tools import search_saved as real_search_saved  # noqa: E402

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------
QUERY_VEC = [1.0, 0.0, 0.0]
CHUNK_VECS = {"near": [1.0, 0.0, 0.0], "mid": [1.0, 1.0, 0.0], "far": [0.3, 1.0, 0.0]}


def fake_embed(texts):
    return [QUERY_VEC for _ in texts]


def fake_embed_timeout(texts):
    raise TimeoutError("fake embedding timeout")


class FakeModel:
    """Stands in for model.get_response. Same signature."""

    GOOD_DIGEST = json.dumps({"summary": "Fake summary sentence one. Fake sentence two.",
                              "tags": ["fake", "offline", "test"], "content_type": "article"})
    GOOD_ANSWER = json.dumps({"answer": "Fake grounded answer [1].", "used_refs": [1]})
    GOOD_REASON = "Fake reason from stored summary."

    def __init__(self, mode: str):
        self.mode = mode
        self.calls = 0

    def _good(self, instructions, json_mode):
        if not json_mode:
            return self.GOOD_REASON
        return self.GOOD_ANSWER if "used_refs" in instructions else self.GOOD_DIGEST

    def __call__(self, instructions, text, json_mode=False, on_usage=None):
        self.calls += 1
        if self.mode == "ok":
            return self._good(instructions, json_mode)
        if self.mode == "error":
            raise RuntimeError("fake model error")
        if self.mode == "timeout":
            raise LLMTimeOutException("fake model timeout")
        if self.mode == "empty":
            return ""
        if self.mode == "bad_json":
            return "this is not json" if json_mode else self.GOOD_REASON
        if self.mode == "bad_ref":  # valid JSON, but cites a source that was never in the context
            if json_mode and "used_refs" in instructions:
                return json.dumps({"answer": "Made-up answer [9].", "used_refs": [9]})
            return self._good(instructions, json_mode)
        if self.mode == "bad_then_ok":
            if self.calls == 1:
                return "this is not json" if json_mode else self.GOOD_REASON
            return self._good(instructions, json_mode)
        raise ValueError(f"unknown fake_model {self.mode!r}")


def fake_fetch_factory(pages: dict):
    def fake_fetch(url):
        kind = pages.get(url, "not_found")
        if kind == "ok":
            text = f"Readable offline article for {url}. " * 20
            html = f"<html><title>Offline {url}</title><body>{text}</body></html>".encode()
            return FetchResult(ok=True, title=f"Offline {url}", text=text, raw_html=html,
                               content_sha256=uuid.uuid4().hex)
        errors = {"not_found": "http_404", "paywall": "too_little_text", "network": "network"}
        return FetchResult(ok=False, error=errors.get(kind, kind))
    return fake_fetch


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
def seed(setup: dict, now: datetime, collection) -> list[str]:
    conn = connect()
    connect_events().close()
    connect_review().close()
    ids = []
    for i, it in enumerate(setup.get("items", [])):
        url = it.get("url", f"https://example{i}.com/item{i}")
        item_id = it.get("id", f"item{i:02d}")
        status = it.get("status", "digested")
        digest_json = None
        if status == "digested":
            digest_json = SavedItemDigest(summary=it.get("summary", f"Summary of item {i}."),
                                          tags=it.get("tags", ["tag1", "tag2", "tag3"]),
                                          content_type="article").model_dump_json()
        saved_at = (now - timedelta(days=it.get("days_ago", 30 - i))).isoformat()
        domain = url.split("/")[2]
        conn.execute(
            "INSERT INTO saved_items (id, url, normalized_url, domain, title, content_text, digest_json, "
            "status, error, saved_at, saved_at_origin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'LIVE')",
            (item_id, url, url.split("://", 1)[1].rstrip("/"), domain, it.get("title", f"Item {i}"),
             it.get("content", f"Content of item {i}."), digest_json, status, it.get("error"), saved_at))
        ids.append(item_id)
    for idx in setup.get("opened", []):
        conn.execute("INSERT INTO item_opens (item_id, opened_at) VALUES (?, ?)", (ids[idx], now.isoformat()))
    for idx, days in setup.get("recommended_days_ago", {}).items():
        conn.execute("INSERT INTO review_recommendations (request_id, item_id, recommended_at) VALUES (?, ?, ?)",
                     ("seed", ids[int(idx)], (now - timedelta(days=days)).isoformat()))
    conn.commit()

    for n, ch in enumerate(setup.get("chunks", [])):
        row = conn.execute("SELECT url, domain, saved_at FROM saved_items WHERE id = ?",
                           (ids[ch["item"]],)).fetchone()
        collection.add(ids=[f"c{n}"], documents=[ch.get("text", f"chunk {n} text")],
                       embeddings=[CHUNK_VECS[ch.get("distance", "near")]],
                       metadatas=[{"item_id": ids[ch["item"]], "url": row["url"], "domain": row["domain"],
                                   "saved_day": int(row["saved_at"][:10].replace("-", ""))}])
    conn.close()
    return ids


# ---------------------------------------------------------------------------
# Run one case
# ---------------------------------------------------------------------------
def http_bridge(client, mode: str = "ok"):
    """bot.requests.post -> TestClient.post. Keeps path and JSON body, drops timeout.
    mode=timeout/down simulates the API not answering, the way requests would fail."""
    def post(url, json=None, timeout=None, **_):
        if mode == "timeout":
            raise bot.requests.Timeout(f"fake: no reply from {url} within {timeout}s")
        if mode == "down":
            raise bot.requests.ConnectionError(f"fake: connection refused {url}")
        path = "/" + url.split("://", 1)[1].split("/", 1)[1]
        return client.post(path, json=json)
    return post


def fill(text: str, ids: list[str], last_request_id: str | None) -> str:
    text = re.sub(r"\{item:(\d+)\}", lambda m: ids[int(m.group(1))], text)
    return text.replace("{last_request_id}", last_request_id or "NO_REQUEST_ID_YET")


def check_db(expect: dict, ids: list[str]) -> list[str]:
    errors = []
    conn = connect()
    for table in ("review_recommendations", "item_opens", "request_events", "saved_items"):
        if table in expect:
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if table == "review_recommendations":
                n = conn.execute("SELECT COUNT(*) FROM review_recommendations WHERE request_id != 'seed'"
                                 ).fetchone()[0]
            if n != expect[table]:
                errors.append(f"db {table}: expected {expect[table]} rows, got {n}")
    for idx, status in expect.get("item_status", {}).items():
        row = conn.execute("SELECT status FROM saved_items WHERE id = ?", (ids[int(idx)],)).fetchone()
        got = row["status"] if row else None
        if got != status:
            errors.append(f"item {idx} status: expected {status}, got {got}")
    if "feedback" in expect:
        n = conn.execute("SELECT COUNT(*) FROM request_events WHERE feedback IS NOT NULL").fetchone()[0]
        if n != expect["feedback"]:
            errors.append(f"db feedback: expected {expect['feedback']} rows, got {n}")
    for url, want in expect.get("urls", {}).items():
        row = conn.execute("SELECT status, content_text FROM saved_items WHERE url = ?", (url,)).fetchone()
        if not row:
            errors.append(f"url {url}: no saved item")
            continue
        if "status" in want and row["status"] != want["status"]:
            errors.append(f"url {url} status: expected {want['status']}, got {row['status']}")
        if "has_content" in want and bool(row["content_text"]) != want["has_content"]:
            errors.append(f"url {url} has_content: expected {want['has_content']}")
    conn.close()
    return errors


def run_case(case: dict) -> dict:
    from starlette.testclient import TestClient

    started = time.perf_counter()
    result = {"id": case["id"], "category": case.get("category", ""), "passed": False,
              "errors": [], "replies": []}
    model = FakeModel(case.get("fake_model", "ok"))
    embed = fake_embed_timeout if case.get("embed") == "timeout" else fake_embed
    with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
        db_path = os.path.join(tmp, "workflow.db")
        collection = _new_collection()
        patches = [
            mock.patch.object(db, "DB_PATH", db_path),
            mock.patch.object(api, "chroma_collection", collection),
            mock.patch.object(api, "fetch_url", fake_fetch_factory(case.get("setup", {}).get("pages", {}))),
            mock.patch.object(api, "save_snapshot", lambda item_id, snap: f"{item_id}.html"),
            # Indexing a new save needs real chunking/embedding; workflow cases test the chat flow, not indexing.
            mock.patch.object(api, "process_document", lambda ids: None),
            mock.patch.object(api, "build_index", lambda *a, **k: None),
            # The model is bound as a default argument, so wrap each caller instead of patching model.get_response.
            mock.patch.object(api, "digest", lambda text: real_digest(text, call_model=model)),
            mock.patch.object(api, "review_reason", lambda row: real_review_reason(row, call_model=model)),
            mock.patch.object(api, "answer", lambda q, col, **kw: real_answer(q, col, embed=embed,
                                                                             call_model=model, **kw)),
            mock.patch.object(api, "search_saved", lambda **kw: real_search_saved(embed=embed, **kw)),
        ]
        for p in patches:
            stack.enter_context(p)
        try:
            ids = seed(case.get("setup", {}), datetime.now(timezone.utc), collection)
            client = stack.enter_context(TestClient(api.app, raise_server_exceptions=False))
            stack.enter_context(mock.patch.object(bot.requests, "post", http_bridge(client, case.get("api", "ok"))))

            last_request_id = None
            for n, step in enumerate(case["steps"], 1):
                text = fill(step["send"], ids, last_request_id)
                reply = bot.dispatch(text)
                result["replies"].append({"send": text, "reply": reply})
                m = re.search(r"Request ID: (\S+)", reply or "")
                if m:
                    last_request_id = m.group(1)
                for s in step.get("expect_contains", []):
                    if s not in (reply or ""):
                        result["errors"].append(f"step {n}: reply missing {s!r}")
                for s in step.get("expect_not_contains", []):
                    if s in (reply or ""):
                        result["errors"].append(f"step {n}: reply should not contain {s!r}")

            result["errors"] += check_db(case.get("expect_db", {}), ids)
            if "expect_model_calls" in case and model.calls != case["expect_model_calls"]:
                result["errors"].append(f"model calls: expected {case['expect_model_calls']}, got {model.calls}")
        except Exception:
            result["errors"].append("runner crash:\n" + traceback.format_exc())
        _chroma.delete_collection(collection.name)

    result["model_calls"] = model.calls
    result["passed"] = not result["errors"]
    result["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def load_cases(only: list[str]) -> list[dict]:
    cases = []
    with CASES_PATH.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{CASES_PATH.name} line {line_no}: {e}")
    seen = [c["id"] for c in cases]
    dupes = {i for i in seen if seen.count(i) > 1}
    if dupes:
        raise SystemExit(f"duplicate case ids: {sorted(dupes)}")
    return [c for c in cases if not only or c["id"] in only]


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=BASE_DIR,
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def main(argv: list[str]) -> int:
    cases = load_cases(argv)
    results = [run_case(c) for c in cases]
    passed = sum(r["passed"] for r in results)
    by_category = {}
    for r in results:
        cat = by_category.setdefault(r["category"], {"passed": 0, "total": 0})
        cat["total"] += 1
        cat["passed"] += r["passed"]

    report = {"run_at": datetime.now(timezone.utc).isoformat(), "git_commit": git_commit(),
              "cases_file": str(CASES_PATH.relative_to(BASE_DIR)), "passed": passed,
              "total": len(results), "by_category": by_category, "results": results}
    if not argv:  # only a full run overwrites the saved evidence
        RESULTS_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for r in results:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['id']:<5} {r['category']:<18} {r['latency_ms']:>7} ms")
        for e in r["errors"]:
            print("      - " + e.replace("\n", "\n        "))
    print(f"\n{passed}/{len(results)} passed" + ("" if argv else f"  -> {RESULTS_PATH.relative_to(BASE_DIR)}"))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
