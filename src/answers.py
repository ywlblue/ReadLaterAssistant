from pydantic import BaseModel

from embeddings import embed_texts
from index import retrieve, set_up_chroma
from model import get_response
from prompts import query_prompt


class Source(BaseModel):
    ref: int
    item_id: str
    url: str
    excerpt: str


class Answer(BaseModel):
    answer: str
    sources: list[Source]


class LLMAnswer(BaseModel):
    answer: str
    used_refs: list[int]


def answer(query, collection, k=5, embed=embed_texts, call_model=get_response, **filters) -> Answer:
    results = retrieve(query, collection, k, embed, **filters)
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
    raw_response = call_model(prompt, question, json_mode=True)
    llm_result = LLMAnswer.model_validate_json(raw_response)
    used_refs = list(dict.fromkeys(llm_result.used_refs))

    if any(ref not in context_map for ref in used_refs):
        raise ValueError("LLM returned an unknown source reference")

    return Answer(
        answer=llm_result.answer,
        sources=[
            Source(
                ref=ref,
                item_id=context_map[ref]["item_id"],
                url=context_map[ref]["url"],
                excerpt=context_map[ref]["text"],
            )
            for ref in used_refs
        ],
    )


if __name__ == '__main__':
    collection = set_up_chroma()
    llm_answer = answer("What is the difference between TCP and UDP?", collection)
    print(llm_answer)
