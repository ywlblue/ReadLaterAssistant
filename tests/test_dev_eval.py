import math

import chromadb
import pytest

from index import retrieve
import sqlite3

from run_dev_eval import (check_frozen, dense_abstain, evaluate_one, filter_violations, queries_path,
                          reciprocal_rank, summarize, top_unique_items)

client = chromadb.EphemeralClient()


def fake_embed(texts):
    # Every query points at angle 0, so smaller angle = closer chunk.
    return [[1.0, 0.0] for _ in texts]


def at_angle(degrees):
    rad = math.radians(degrees)
    return [math.cos(rad), math.sin(rad)]


@pytest.fixture
def collection():
    # Chunks a1..a3 all belong to it1 and take the 3 closest slots.
    rows = [("a1", "it1", 1), ("a2", "it1", 2), ("a3", "it1", 3),
            ("b1", "it2", 4), ("c1", "it3", 5), ("d1", "it4", 6),
            ("e1", "it5", 7), ("f1", "it6", 8)]
    collection = client.get_or_create_collection(name="dev_eval", metadata={"hnsw:space": "cosine"})
    collection.upsert(
        ids=[r[0] for r in rows],
        documents=[f"doc {r[0]}" for r in rows],
        embeddings=[at_angle(r[2]) for r in rows],
        metadatas=[{"item_id": r[1], "url": f"https://{r[1]}.com", "domain": f"{r[1]}.com",
                    "saved_day": 20261020} for r in rows],
    )
    yield collection
    client.delete_collection(collection.name)


def row(**kw):
    base = {"id": "t", "query": "q", "type": "find", "filters": None,
            "answerable": True, "expected_item_ids": []}
    return {**base, **kw}


def test_top_unique_items_keeps_order():
    chunks = [{"item_id": i} for i in ["x", "x", "y", "x", "z"]]
    assert top_unique_items(chunks, 2) == ["x", "y"]


def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b", "c"], ["c"]) == pytest.approx(1 / 3)
    assert reciprocal_rank(["a", "b", "c"], ["b", "c"]) == 0.5
    assert reciprocal_rank(["a"], ["z"]) == 0.0


def fake_search(collection):
    return lambda q, k, **f: retrieve(q, collection, k, embed=fake_embed, **f)


def test_dedup_before_top5(collection):
    # it5 is the 7th chunk but the 5th distinct item, so it counts as a hit.
    r = evaluate_one(row(expected_item_ids=["it5"]), top_items=5, chunk_k=30, search=fake_search(collection),
                     abstain=dense_abstain())
    assert r["retrieved_item_ids"] == ["it1", "it2", "it3", "it4", "it5"]
    assert r["hit"] and r["first_hit_rank"] == 5
    assert r["reciprocal_rank"] == pytest.approx(0.2)


def test_item_after_top5_is_a_miss(collection):
    r = evaluate_one(row(expected_item_ids=["it6"]), top_items=5, chunk_k=30, search=fake_search(collection),
                     abstain=dense_abstain())
    assert not r["hit"] and r["reciprocal_rank"] == 0.0 and r["outcome"] == "Failed"


def test_no_evidence_abstains(collection):
    r = evaluate_one(row(answerable=False), search=fake_search(collection), abstain=dense_abstain(0.0))
    assert r["abstained"] and r["outcome"] == "Pass"
    assert "hit" not in r


def test_no_evidence_not_abstained(collection):
    r = evaluate_one(row(answerable=False), search=fake_search(collection), abstain=dense_abstain(0.6))
    assert not r["abstained"] and r["outcome"] == "Failed"


def test_summary_keeps_groups_apart():
    results = [
        {"answerable": True, "hit": True, "reciprocal_rank": 1.0, "abstained": False},
        {"answerable": True, "hit": False, "reciprocal_rank": 0.0, "abstained": True},
        {"answerable": False, "abstained": True},
    ]
    s = summarize(results)
    assert s["hit@5"] == 0.5 and s["mrr"] == 0.5
    assert s["answerable_abstained"] == 1
    assert (s["no_evidence"], s["no_evidence_abstained"]) == (1, 1)


def test_final_test_split_is_locked_by_default():
    with pytest.raises(SystemExit):
        queries_path("test")


def test_final_test_split_opens_with_flag():
    assert queries_path("test", final_test=True).name == "test.jsonl"
    assert queries_path("dev").name == "dev.jsonl"


def test_check_frozen(tmp_path):
    cases = tmp_path / "dev.jsonl"
    cases.write_text('{"id": "q01"}\n', encoding="utf-8")
    import hashlib, json
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"splits": {"dev": {"sha256": hashlib.sha256(cases.read_bytes()).hexdigest()}}}))

    check_frozen("dev", cases, manifest)  # unchanged: no error

    cases.write_text('{"id": "q01", "query": "edited"}\n', encoding="utf-8")
    with pytest.raises(SystemExit):
        check_frozen("dev", cases, manifest)


@pytest.fixture
def items_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE saved_items (id TEXT PRIMARY KEY, domain TEXT, saved_at TEXT)")
    conn.executemany("INSERT INTO saved_items VALUES (?, ?, ?)", [
        ("it1", "go.dev", "2026-10-12T09:00:00"),
        ("it2", "go.dev", "2026-10-18T09:00:00"),
        ("it3", "example.com", "2026-10-15T09:00:00"),
    ])
    yield conn
    conn.close()


def test_filter_violations_domain(items_db):
    assert filter_violations(items_db, ["it1", "it2", "it3"], {"domain": "go.dev"}) == ["it3"]


def test_filter_violations_date_range_is_inclusive(items_db):
    assert filter_violations(items_db, ["it1", "it2", "it3"], {"since": 20261012, "until": 20261015}) == ["it2"]


def test_filter_violations_unknown_item_counts(items_db):
    assert filter_violations(items_db, ["it1", "ghost"], {"domain": "go.dev"}) == ["ghost"]


def test_filter_violations_no_filters(items_db):
    assert filter_violations(items_db, ["it3"], None) == []


def test_filter_check_uses_all_returned_items(collection):
    # Out-of-filter item at chunk position 8 (after the top 5 items) must still be caught.
    search = lambda q, k, **f: retrieve(q, collection, k, embed=fake_embed)
    row = {"id": "f1", "query": "q", "type": "filter", "filters": {"domain": "it1.com"},
           "answerable": True, "expected_item_ids": ["it1"]}
    seen = {}

    def check(item_ids, filters):
        seen["ids"] = item_ids
        return [i for i in item_ids if i != "it1"]

    result = evaluate_one(row, search, dense_abstain(), check_filters=check)
    assert "it6" in seen["ids"]
    assert "it6" in result["filter_violations"]


def test_summary_counts_filter_cases():
    results = [
        {"answerable": True, "hit": True, "reciprocal_rank": 1.0, "abstained": False, "filter_violations": []},
        {"answerable": True, "hit": True, "reciprocal_rank": 1.0, "abstained": False, "filter_violations": ["x"]},
        {"answerable": True, "hit": True, "reciprocal_rank": 1.0, "abstained": False, "filter_violations": None},
    ]
    s = summarize(results)
    assert (s["filter_cases"], s["filter_correct"]) == (2, 1)
