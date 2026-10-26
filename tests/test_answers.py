import json

import chromadb
import pytest
from pydantic import ValidationError

from answers import answer

client = chromadb.EphemeralClient()


def fake_embed(texts): return [[1.0, 0.0, 0.0] for _ in texts]


def fake_call_model_1(instructions, query, json_mode): return json.dumps(
    {"answer": "UDP is connectionless [1].", "used_refs": [1]})


def fake_call_model_2(instructions, query, json_mode): return json.dumps(
    {"answer": "UDP is connectionless [2].", "used_refs": [2]})


def fake_call_model_invalid_ref(instructions, query, json_mode): return json.dumps(
    {"answer": "UDP is connectionless [9].", "used_refs": [9]})


def fake_call_model_invalid_json(instructions, query, json_mode): return "Hello World"


@pytest.fixture
def collection():
    collection = client.get_or_create_collection(name="test", metadata={"hnsw:space": "cosine"})
    documents = ["UDP is connectionless.", "TCP is reliable."]
    collection.upsert(ids=["a1", "b1"],
                      documents=documents,
                      embeddings=fake_embed(documents),
                      metadatas=[{"domain": "go.dev", "saved_day": 20261012, "item_id": "A",
                                  "url": "https://www.test-A.com"},
                                 {"domain": "go.dev", "saved_day": 20261018, "item_id": "B",
                                  "url": "https://www.test-B.com"}
                                 ])

    yield collection
    client.delete_collection(collection.name)


def test_answer_success_with_ref_1(collection):
    result = answer("Test question", collection, embed=fake_embed, call_model=fake_call_model_1)
    assert len(result.sources) == 1
    assert result.sources[0].ref == 1

    source = result.sources[0]
    assert source.item_id == "A"
    assert source.url == "https://www.test-A.com"
    assert source.excerpt == "UDP is connectionless."


def test_answer_success_with_ref_2(collection):
    result = answer("Test question", collection, embed=fake_embed, call_model=fake_call_model_2)
    assert len(result.sources) == 1
    assert result.sources[0].ref == 2

    source = result.sources[0]
    assert source.item_id == "B"
    assert source.url == "https://www.test-B.com"
    assert source.excerpt == "TCP is reliable."


def test_answer_failed_with_invalid_ref(collection):
    with pytest.raises(ValueError):
        answer("Test question", collection, embed=fake_embed, call_model=fake_call_model_invalid_ref)


def test_answer_failed_with_invalid_json(collection):
    with pytest.raises(ValidationError):
        answer("Test question", collection, embed=fake_embed, call_model=fake_call_model_invalid_json)
