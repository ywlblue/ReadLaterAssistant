import os

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from storage import connect

QUERY_TEMPLATE = """Given the context, answer the question. 
Only use the context below. If the answer is not in the context, say you don’t know.
Respond in exactly {num_sentences} sentences.
Context: {context}\n
Question: {question}\n
"""

query_template = PromptTemplate(template=QUERY_TEMPLATE, input_variables=["num_sentences", "context", "question"])

load_dotenv()


def load_document(data: str, item_id: str, url: str) -> Document:
    return Document(
        page_content=data,
        metadata={"item_id": item_id, "url": url},
    )


def split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=50,
        length_function=len,
    )
    return splitter.split_documents(docs)


def embed_chunks(chunks: list[Document]) -> list[list[float]]:
    if not chunks:
        return []

    embedding = OpenAIEmbeddings(
        model="text-embedding-3-small",
    )
    texts = [chunk.page_content for chunk in chunks]
    return embedding.embed_documents(texts)


if __name__ == '__main__':
    conn = connect()
    rows = conn.execute("""
                        SELECT id, url, content_text
                        FROM saved_items
                        WHERE id IN ('2431fbb46605e2f9', 'ce6513377c2b650f', '8d3838e130953273', 
                        '1e122840bf42ea63', 'b6b726c7e072489e');
                        """
                        ).fetchall()
    conn.close()

    if not rows:
        raise ValueError("Item not found.")

    documents = []
    for row in rows:
        documents.append(load_document(
            data=row["content_text"],
            item_id=str(row["id"]),
            url=row["url"],
        ))

    split_chunks = split_documents(documents)

    embedding = OpenAIEmbeddings(model="text-embedding-3-small", )
    vector_store = InMemoryVectorStore(embedding=embedding)
    vector_store.add_documents(documents=split_chunks)

    question = "Who was Tutankhamun’s mother?"
    results = vector_store.similarity_search_with_score(
        query=question,
        k=2,
    )

    context = "\n\n".join(
        f"Source: {doc.metadata.get('url', '')}\n{doc.page_content}"
        for doc, _ in results
    )

    llm = ChatOpenAI(model=os.environ["OPENAI_MODEL"])
    parser = StrOutputParser()

    chain = query_template | llm | parser

    result = chain.invoke({"num_sentences": 5, "context": context, "question": question})
    print(result)
