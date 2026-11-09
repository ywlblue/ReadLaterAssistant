# Hybrid review and failure cases (Sun 11/8)

Review of the 11/7 dev runs (dev split only, 30 cases).

- Code: commit `8c0376a` (hybrid search). Results: commit `b21d7fb`.
- Files: `2026-11-07_dev_{dense,lexical,hybrid}_eval.jsonl`
- Corpus: v2026-11-07, 2216 chunks. Abstain rule: dense top-1 distance >= 0.6.

## Summary

| Method  | Hit@5 | MRR   | No-evidence abstain | Mean latency |
|---------|-------|-------|---------------------|--------------|
| dense   | 1.0   | 0.951 | 5/6                 | 285 ms       |
| lexical | 1.0   | 0.948 | 0/6                 | 3 ms         |
| hybrid  | 1.0   | 0.972 | 5/6                 | 429 ms       |

Only one case has `outcome: Failed` in hybrid: **q17**.

## Where the methods differ

| Case | Type        | Rank dense / lexical / hybrid | Note |
|------|-------------|-------------------------------|------|
| q05  | vague       | 2 / 1 / **1**                 | Hybrid fixed it. Lexical helped. |
| q27  | filter      | 1 / 2 / **1**                 | Hybrid kept the dense rank. |
| q24  | find        | 3 / 4 / **3**                 | All weak. Hybrid did not help. |
| q17  | no_evidence | did not abstain (all 3)       | The only failed case. |

All other cases are rank 1 in all three methods.

## Failure 1: q17, near-topic question with no answer

- Query: "How does QUIC's handshake work?"
- No saved item covers QUIC. Expected: abstain.
- Top results: "Domain Name System - Wikipedia", "Chapter 2 DNS Concepts",
  "Reliability and Congestion Avoidance over UDP".
- Top distance 0.585 < 0.6, so it did **not** abstain.
- Why: the library has many networking articles. The topic is close, but none answers the question.
- Lesson: one distance threshold cannot tell "close topic" from "has the answer".
  Lowering the threshold would also hurt q29 (0.575) and q10 (0.590).
- Possible fix (later, not today): let the Ask step check the passages and say
  "not enough evidence" if they do not answer the question.

## Failure 2: q24, broad question, correct item at rank 3

- Query: "How to deploy a web application?"
- Expected: two Heroku articles (`110a083f…`, `267e3396…`).
- Hybrid top 2:
  1. "Java EE Tutorial Release 7 - Contents" (docs.oracle.com). A table of contents page that matches many words.
  2. "Deploy WAR to Amazon AWS EC2" (appsdeveloperblog.com).
- Rank 2 is also about deploying a web app. **The gold label may be incomplete.**
- To do (Mon 11/9 audit): decide if `8432857d…` should be added as a valid item.
  Do not change the frozen final-test split.
- Note: the Java EE contents page is a "hub page" that is noise for broad queries.

## Risk 3: q29 and q10, correct but close to the threshold

- q29 "the king who has lots of wives" → Henry VIII article, rank 1, distance **0.575**.
- q10 Twilio webhook question → SendGrid webhook doc, rank 1, distance **0.590**.
- Both pass now. A slightly different wording could push them over 0.6, and `/ask` would refuse.
- Related to the optional query-rewriting idea on Thu 11/12.

## Other notes

- q16, q18–q20 return 5 items, but `abstained: true`. This is expected:
  retrieval always returns top-k, and the abstain check decides afterwards.
- Lexical never abstains (0/6). Hybrid must keep using the dense distance for abstention.
- Open TODO from 11/7: if lexical or hybrid is selected, `/save` must also update `chunks_fts`.

## Final-test check

- `run_dev_eval.py` uses `--split dev` by default. `--split test` exits unless `--final-test` is passed.
- Split files are checked against the sha256 in `eval/dataset-manifest.json`.
- `eval/results/` has no test-split result files. Final-test results were not used.
