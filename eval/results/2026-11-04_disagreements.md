# Dense vs lexical: 5 disagreements (dev split)

Source: `eval/results/2026-11-05_dev_{dense,lexical}_eval.jsonl` (commit 483e702; identical to the 11/4 runs).
Summary table: `eval/dev-comparison.csv`. Only 5/30 cases get the exact same top-5 from both methods,
but both reach Hit@5 = 1.000, so most disagreements are in ranks 2-5.

| id | type | dense first hit | lexical first hit | dense top distance |
|---|---|---|---|---|
| q05 | vague | 2 | 1 | 0.528 |
| q27 | filter | 1 | 2 | 0.544 |
| q24 | find (2 gold items) | 3 | 4 | 0.451 |
| q29 | vague | 1 | 1 (different ranks 2-5) | 0.575 |
| q17 | no_evidence | did not abstain | did not abstain | 0.585 |

## q05 - "There's an ariticle about the IOC using Factory design pattern." (lexical wins)
- Gold: `40a58d` Essential Java Design Principles (java-design-patterns.com).
- Dense rank 1 is `8cf732` Fowler's *Inversion of Control Containers and the Dependency Injection pattern*: the closest *topic*, but not the article I meant. Gold is rank 2.
- Lexical puts gold at rank 1: the exact words "IOC" and "Factory" appear together in the gold article.
- Lesson: when the user remembers a specific term, exact-word matching beats meaning matching. The typo "ariticle" did not hurt either method.

## q27 - "Give me a high level Python tutorial" + date filter 10/17-10/19 (dense wins)
- Gold: `46da2d` Python docs, *9. Classes*.
- The filter leaves only ~5 items, so both methods hit; the order is what differs.
- Lexical rank 1 is `ffac87` Simon Willison's LLM post: it says "Python" many times. Dense understands "Python tutorial" as a request for documentation.
- Lesson: frequent words can fool BM25; meaning helps for generic requests.

## q24 - "How to deploy a web application?" (both weak, label question)
- Gold: two Heroku articles (`110a08`, `267e33`). Dense finds them at 3 and 5, lexical at 4 and 5.
- Both methods put `843285` *Deploy WAR to AWS EC2* and `8d3838` *Java EE Tutorial* above them. `843285` is arguably a correct answer too.
- Lesson: for a broad question, the gold labels are narrower than "what I would accept". This is a labeling limit, not only a retrieval failure. Dev labels are frozen, so it stays as a known limitation (MRR is pessimistic here).

## q29 - "What's the article about the king who has lots of wives?" (same answer, different risk)
- Both rank gold `e8cd23` *Behind the Throne: Henry VIII* at 1; ranks 2-5 are unrelated in both.
- Lexical finds it through the words "king" / "wives" in the text. Dense finds it through meaning, but with distance 0.575, close to the 0.6 refusal threshold.
- Lesson: dense is right but only just; a slightly different wording could make `/ask` refuse. Candidate for the Thu 11/12 query-rewriting experiment.

## q17 - "How does QUIC's handshake work?" (no-evidence; both fail, for different reasons)
- No saved article covers QUIC. Correct behaviour: abstain.
- Dense: top distance 0.585 (DNS / UDP / HTTP-connection articles) is below 0.6, so it does not abstain. Same miss as on 11/2.
- Lexical: abstains only when nothing matches. Common words ("how", "work", "handshake") always match something, so lexical abstains on 0/6 no-evidence cases.
- Lesson: lexical has no built-in "not found" signal, and BM25 scores are not on a fixed scale. For Saturday's hybrid (RRF), RRF keeps only ranks, so the abstain decision must still come from the dense distance (or a separate rule).

## Takeaways for hybrid (Sat 11/7)
1. Lexical helps exact-term memories (q05); dense helps generic or paraphrased requests (q27). Combining them is reasonable.
2. Abstention cannot come from RRF scores; keep the dense distance check.
3. Hit@5 is already 1.000 for both, so hybrid can only show up in MRR and abstention. No improvement is guaranteed.
