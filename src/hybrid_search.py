from typing import Any

from build_fts import lexical_search
from embeddings import embed_texts
from index import make_dense_search

RRF_K = 60


def rrf(lexical: dict, dense: dict, k: int = RRF_K) -> list[tuple[str, float]]:
    scores = {}
    for ranks in (lexical, dense):
        for item_id, rank in ranks.items():  # rank starts from 0
            scores[item_id] = scores.get(item_id, 0) + 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))


#  Keep order, drop repeats by item_id
def item_ranks(data: list[dict]) -> dict:
    items = dict.fromkeys(d["item_id"] for d in data)
    return {item_id: index for index, item_id in enumerate(items)}


def make_hybrid_search(collection, embed=embed_texts, rrf_k: int = RRF_K):
    dense_search = make_dense_search(collection, embed)

    def search(query: str, k: int, **filters) -> list[dict[str, Any | None]]:
        lex_chunks = lexical_search(query, k, **filters)
        dense_chunks = dense_search(query, k, **filters)
        best_chunk = {}
        for c in dense_chunks + lex_chunks:
            best_chunk.setdefault(c["item_id"], c)
        top_distance = dense_chunks[0]["distance"] if dense_chunks else None
        fused = rrf(item_ranks(lex_chunks), item_ranks(dense_chunks), rrf_k)
        return [{**best_chunk[i], "rrf_score": s, "distance": top_distance}
                for i, s in fused]

    return search
