import hashlib
import sqlite3
from dataclasses import dataclass
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from db import get_connection

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL REFERENCES saved_items(id),
    content_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    strategy TEXT,
    UNIQUE(item_id, chunk_index, strategy)
)
"""


@dataclass
class Strategy:
    name: str = "recursive"
    chunk_size: int = 1000
    chunk_overlap: int = 50

    @property
    def strategy_info(self):
        return f"{self.name}_{self.chunk_size}_{self.chunk_overlap}"


def connect_chunks(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = get_connection(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def load_document(data: str, item_id: str, url: str) -> Document:
    return Document(
        page_content=data,
        metadata={"item_id": item_id, "url": url},
    )


def split_documents_with_strategy(docs: list[Document], strategy: Strategy) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", ". ", "！", "？", " ", ""],
        chunk_size=strategy.chunk_size,
        chunk_overlap=strategy.chunk_overlap,
        length_function=len,
    )
    return splitter.split_documents(docs)


def get_document_id(item_id: str, strategy: str, chunk_index: int, text_sha: str):
    context = f"{item_id}:{strategy}:{chunk_index}:{text_sha}"
    return hashlib.sha256(context.encode()).hexdigest()


def process_document(item_ids: list[str]):
    if not item_ids:
        return

    placeholders = ",".join(["?"] * len(item_ids))
    query = f"""
        SELECT * FROM saved_items
        WHERE id IN ({placeholders})
          AND content_text IS NOT NULL
          AND TRIM(content_text) != ''
    """

    conn = connect_chunks()
    rows = conn.execute(query, item_ids).fetchall()
    split_strategy = Strategy()
    for row in rows:
        document = load_document(row["content_text"], row["id"], row["url"])
        strategy_info = split_strategy.strategy_info
        split_docs = split_documents_with_strategy([document], strategy=split_strategy)
        text_sha = hashlib.sha256(row["content_text"].encode()).hexdigest()
        for index, doc in enumerate(split_docs):
            doc_id = get_document_id(row["id"], strategy_info, index, text_sha)
            conn.execute("INSERT OR IGNORE INTO chunks (id, item_id, content_text, chunk_index, strategy) VALUES (?, "
                         "?, ?, ?, ?)", (doc_id, row["id"], doc.page_content, index, strategy_info))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    conn = connect_chunks()
    chunk_rows = conn.execute("SELECT id FROM saved_items WHERE content_text IS NOT NULL").fetchall()
    item_ids = [row["id"] for row in chunk_rows]
    process_document(item_ids)
    rows = conn.execute("SELECT item_id, COUNT(*) FROM chunks GROUP BY item_id;").fetchall()
    for row, count in rows:
        print(f"{row}: {count}")
    conn.close()
