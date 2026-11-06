from compare_dev import method_row, same_top5_count


def row(id, answerable, rr=0.0, abstained=False, latency=10.0, retrieved=("a",)):
    r = {"id": id, "answerable": answerable, "abstained": abstained,
         "latency_ms": latency, "retrieved_item_ids": list(retrieved)}
    if answerable:
        r.update({"hit": rr > 0, "reciprocal_rank": rr})
    return r


def test_method_row_splits_answerable_and_no_evidence():
    rows = [row("q1", True, rr=1.0), row("q2", True, rr=0.5), row("q3", False, abstained=True, latency=40.0)]
    out = method_row("dense", rows)
    assert out["answerable"] == 2 and out["no_evidence"] == 1
    assert out["hit@5"] == 1.0
    assert out["mrr"] == 0.75
    assert out["no_evidence_abstained"] == 1
    assert out["mean_latency_ms"] == 20.0


def test_same_top5_count_needs_identical_order():
    dense = [row("q1", True, 1.0, retrieved=("a", "b")), row("q2", True, 1.0, retrieved=("a", "b"))]
    lexical = [row("q1", True, 1.0, retrieved=("a", "b")), row("q2", True, 1.0, retrieved=("b", "a"))]
    assert same_top5_count({"dense": dense, "lexical": lexical}) == (1, 2)
