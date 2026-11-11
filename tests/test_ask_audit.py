from types import SimpleNamespace

import run_ask_audit
from answers import Answer, Source


def test_audit_one_counts_tokens_and_gold(monkeypatch):
    def fake_answer(query, collection, call_model, **filters):
        # Simulate two model calls (one malformed-output retry), each reporting usage.
        call_model("i", "t", json_mode=True)
        call_model("i", "t", json_mode=True)
        return Answer(answer="A", top_distance=0.4, sources=[
            Source(ref=1, item_id="gold", url="u", excerpt="e", chunk_id="c1")])

    def fake_get_response(instructions, text, json_mode=False, on_usage=None):
        on_usage(SimpleNamespace(input_tokens=100, output_tokens=20))
        return "{}"

    monkeypatch.setattr(run_ask_audit, "answer", fake_answer)
    monkeypatch.setattr(run_ask_audit, "get_response", fake_get_response)
    row = {"id": "q1", "type": "ask", "query": "q", "filters": {"domain": "d"},
           "expected_item_ids": ["gold"], "supporting_passage": None}

    r = run_ask_audit.audit_one(row, collection=None)
    assert (r["input_tokens"], r["output_tokens"], r["model_calls"]) == (200, 40, 2)
    assert r["cites_gold_item"] is True
    assert r["human_relevant"] is None


def test_cost_usd():
    rows = [{"input_tokens": 1_000_000, "output_tokens": 100_000}]
    assert run_ask_audit.cost_usd(rows, "gpt-4o") == 3.5
    assert run_ask_audit.cost_usd(rows, "unknown-model") is None


def test_audit_ids_are_dev_answerable():
    by_id = {r["id"]: r for r in run_ask_audit.load_queries(run_ask_audit.QUERIES_PATH)}
    assert len(run_ask_audit.AUDIT_IDS) == 10
    assert all(by_id[i]["answerable"] for i in run_ask_audit.AUDIT_IDS)
