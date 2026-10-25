import chromadb
import pytest

from index import retrieve

client = chromadb.EphemeralClient()


def fake_embed(texts): return [[1.0, 0.0, 0.0] for _ in texts]


@pytest.fixture
def collection():
    collection = client.get_or_create_collection(name="test", metadata={"hnsw:space": "cosine"})
    documents = ["doc1", "doc2", "doc3", "doc4"]
    collection.upsert(ids=["a1", "a2", "b1", "b2"],
                      documents=documents,
                      embeddings=fake_embed(documents),
                      metadatas=[{"domain": "go.dev", "saved_day": 20261012, "item_id": "it1",
                                  "url": "https://www.test-it1.com"},
                                 {"domain": "go.dev", "saved_day": 20261018, "item_id": "it2",
                                  "url": "https://www.test-it2.com"},
                                 {"domain": "example.com", "saved_day": 20261015, "item_id": "it3",
                                  "url": "https://www.test-it3.com"},
                                 {"domain": "example.com", "saved_day": 20261020, "item_id": "it4",
                                  "url": "https://www.test-it4.com"}])

    yield collection
    client.delete_collection(collection.name)


def test_retrieve_with_domain(collection):
    results = retrieve("Some questions", collection, 50, embed=fake_embed, domain="go.dev")
    assert {r["item_id"] for r in results} == {"it1", "it2"}
    assert {r["chunk_id"] for r in results} == {"a1", "a2"}


def test_retrieve_with_since(collection):
    results = retrieve("Some questions", collection, 50, embed=fake_embed, since=20261015)
    assert {r["chunk_id"] for r in results} == {"b1", "a2", "b2"}


def test_retrieve_with_since_and_until(collection):
    results = retrieve("Some questions", collection, 50, embed=fake_embed, since=20261013, until=20261018)
    assert {r["chunk_id"] for r in results} == {"b1", "a2"}


def test_retrieve_with_domain_and_since(collection):
    results = retrieve("Some questions", collection, 50, embed=fake_embed, domain="go.dev", since=20261015)
    assert {r["chunk_id"] for r in results} == {"a2"}


