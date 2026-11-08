import pytest

import hybrid_search
from hybrid_search import RRF_K, item_ranks, make_hybrid_search, rrf
from run_dev_eval import dense_abstain, evaluate_one


def chunk(chunk_id, item_id, **extra):
    return {"chunk_id": chunk_id, "item_id": item_id, "text": f"text of {chunk_id}", **extra}


@pytest.fixture
def fake_search(monkeypatch):
    """Replace lexical and dense with fixed lists, and record the args they get.

    Returns a function: setup(lex_chunks, dense_chunks) -> (search, calls).
    No SQLite, no Chroma, no embedding API.
    """
    def setup(lex_chunks, dense_chunks):
        calls = []

        def fake_lexical(query, k, **filters):
            calls.append(("lexical", query, k, filters))
            return lex_chunks

        def fake_make_dense(collection, embed):
            def fake_dense(query, k, **filters):
                calls.append(("dense", query, k, filters))
                return dense_chunks
            return fake_dense

        # Patch the names inside hybrid_search, because it did `from ... import ...`.
        monkeypatch.setattr(hybrid_search, "lexical_search", fake_lexical)
        monkeypatch.setattr(hybrid_search, "make_dense_search", fake_make_dense)
        return make_hybrid_search(collection=None), calls

    return setup


# ---------- rrf / item_ranks (pure functions) ----------

def test_item_in_both_lists_ranks_first():
    fused = rrf({"a": 0, "b": 1}, {"b": 0, "c": 1})
    assert [item_id for item_id, _ in fused] == ["b", "a", "c"]
    # b: 1/61 (dense rank 0) + 1/62 (lexical rank 1)
    assert fused[0][1] == pytest.approx(1 / (RRF_K + 1) + 1 / (RRF_K + 2))


def test_ties_use_item_id_order():
    # Same rank in different lists -> same score; order must not depend on set/hash order.
    assert rrf({"z": 2}, {"y": 2}) == rrf({"z": 2}, {"y": 2})
    assert [item_id for item_id, _ in rrf({"z": 2}, {"y": 2})] == ["y", "z"]


def test_item_ranks_counts_each_item_once():
    chunks = [chunk("x1", "x"), chunk("x2", "x"), chunk("y1", "y"), chunk("x3", "x")]
    assert item_ranks(chunks) == {"x": 0, "y": 1}


def test_empty_inputs():
    assert rrf({}, {}) == []
    assert item_ranks([]) == {}


# ---------- make_hybrid_search ----------

def test_one_row_per_item_and_dense_chunk_preferred(fake_search):
    lex = [chunk("L-a", "a", score=-3.0), chunk("L-b", "b", score=-2.0)]
    dense = [chunk("D-b1", "b", distance=0.30), chunk("D-b2", "b", distance=0.35),
             chunk("D-c", "c", distance=0.50)]
    search, _ = fake_search(lex, dense)

    rows = search("query", 30)

    assert [r["item_id"] for r in rows] == ["b", "a", "c"]
    assert len({r["item_id"] for r in rows}) == len(rows)
    # Item b is in both lists: the representative chunk is the best dense chunk.
    assert rows[0]["chunk_id"] == "D-b1"
    # Item a is lexical-only: its lexical chunk is used.
    assert rows[1]["chunk_id"] == "L-a"
    assert all("rrf_score" in r for r in rows)


def test_distance_is_dense_top1_on_every_row(fake_search):
    lex = [chunk("L-a", "a", score=-3.0)]
    dense = [chunk("D-b", "b", distance=0.42), chunk("D-c", "c", distance=0.55)]
    search, _ = fake_search(lex, dense)

    rows = search("query", 30)

    assert {r["distance"] for r in rows} == {0.42}


def test_filters_and_k_are_passed_to_both(fake_search):
    search, calls = fake_search([], [])

    search("query", 30, domain="example.com", since=20261001, until=20261031)

    expected_filters = {"domain": "example.com", "since": 20261001, "until": 20261031}
    assert ("lexical", "query", 30, expected_filters) in calls
    assert ("dense", "query", 30, expected_filters) in calls


# ---------- abstention through the eval interface ----------

def row(answerable, expected=()):
    return {"id": "q-test", "query": "query", "type": "test", "filters": None,
            "answerable": answerable, "expected_item_ids": list(expected)}


def test_abstains_when_dense_is_far_even_if_lexical_matches(fake_search):
    # Lexical always finds something; the decision must come from dense distance.
    lex = [chunk("L-a", "a", score=-5.0)]
    dense = [chunk("D-b", "b", distance=0.95)]
    search, _ = fake_search(lex, dense)

    result = evaluate_one(row(answerable=False), search=search,
                          abstain=dense_abstain(0.6), search_method="hybrid")

    assert result["abstained"] is True
    assert result["outcome"] == "Pass"


def test_abstains_when_dense_is_empty(fake_search):
    search, _ = fake_search([chunk("L-a", "a", score=-5.0)], [])

    result = evaluate_one(row(answerable=False), search=search,
                          abstain=dense_abstain(0.6), search_method="hybrid")

    assert result["top_distance"] is None
    assert result["abstained"] is True


def test_answerable_case_scores_through_eval(fake_search):
    lex = [chunk("L-a", "a", score=-3.0), chunk("L-b", "b", score=-2.0)]
    dense = [chunk("D-b", "b", distance=0.30), chunk("D-c", "c", distance=0.50)]
    search, _ = fake_search(lex, dense)

    result = evaluate_one(row(answerable=True, expected=["a"]), search=search,
                          abstain=dense_abstain(0.6), search_method="hybrid")

    assert result["retrieved_item_ids"] == ["b", "a", "c"]
    assert result["first_hit_rank"] == 2
    assert result["reciprocal_rank"] == pytest.approx(0.5)
    assert result["abstained"] is False
