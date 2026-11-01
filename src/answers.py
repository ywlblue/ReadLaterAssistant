from pydantic import BaseModel, ValidationError

from embeddings import embed_texts
from index import retrieve, set_up_chroma
from model import get_response
from prompts import query_prompt

# 10/26: answerable top1 max 0.544, no-evidence min 0.585 (n=15). Re-check after 20-q baseline.
MAX_DISTANCE = 0.6


class Source(BaseModel):
    ref: int
    item_id: str
    url: str
    excerpt: str
    chunk_id: str


class Answer(BaseModel):
    answer: str
    sources: list[Source]
    insufficient_evidence: bool = False
    top_distance: float | None = None
    layer: str | None = None


class LLMAnswer(BaseModel):
    answer: str
    used_refs: list[int]


def answer(query, collection, k=5, embed=embed_texts, call_model=get_response, max_distance=MAX_DISTANCE, **filters) -> Answer:
    results = retrieve(query, collection, k, embed, **filters)

    if not results or results[0]["distance"] > max_distance:
        return Answer(answer="No saved item has enough evidence to answer this.",
                      sources=[], insufficient_evidence=True, layer="retrieval",
                      top_distance=results[0]["distance"] if results else None)

    context_map = {
        i: result
        for i, result in enumerate(results, start=1)
    }

    context = "\n\n".join(
        f"[{ref}]\n{result['text']}"
        for ref, result in context_map.items()
    )

    prompt = query_prompt()
    question = f"""
        Context:{context}
        
        Question:{query}
        
        Return the answer as JSON.
        """

    for attempt in range(2):
        raw_response = call_model(prompt, question, json_mode=True)
        try:
            llm_result = LLMAnswer.model_validate_json(raw_response)
            break
        except ValidationError:
            if attempt == 1:
                return Answer(answer="The model returned an invalid response.",
                              sources=[], insufficient_evidence=True,
                              layer="model_error",
                              top_distance=results[0]["distance"])
    used_refs = list(dict.fromkeys(llm_result.used_refs))

    if any(ref not in context_map for ref in used_refs):
        raise ValueError("LLM returned an unknown source reference")

    if not used_refs:
        return Answer(answer=llm_result.answer, sources=[], layer="model",
                      insufficient_evidence=True, top_distance=results[0]["distance"])

    return Answer(
        answer=llm_result.answer,
        sources=[
            Source(
                ref=ref,
                item_id=context_map[ref]["item_id"],
                url=context_map[ref]["url"],
                excerpt=context_map[ref]["text"],
                chunk_id=context_map[ref]["chunk_id"]
            )
            for ref in used_refs
        ],
        top_distance=results[0]["distance"]
    )


if __name__ == '__main__':
    clt = set_up_chroma()
    llm_answer = answer("What is the difference between TCP and UDP?", clt)
    print(llm_answer)
