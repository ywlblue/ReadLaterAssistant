# Evaluation

## Dataset provenance

Source of truth: `eval/dataset-manifest.json`. Check it with
`python src/audit_manifest.py` (read-only; no search, no scoring).

### Split
- 50 cases, frozen 2026-11-03 (commit aff57af): 30 dev / 20 final test.
- Dev: 24 answerable + 6 no-evidence. Test: 16 answerable + 4 no-evidence.
- Test is for Sprint 4 only. `run_dev_eval.py --split test` needs `--final-test`;
  no test results exist yet.

### Where the questions came from
| Origin | Dev | Test | How it was written |
|---|---|---|---|
| hand_authored | 15 | 0 | Written by me from memory of what I saved |
| find_queries.jsonl | 7 | 0 | Earlier hand-written Find queries (10/24) |
| no_evidence.jsonl | 5 | 0 | 10/26 no-evidence fixtures |
| claude_drafted | 3 | 20 | Claude drafted from article title/summary; I picked them |

- Real-use questions (asked through the bot during self-use): **0 so far**.
- New real-use questions go into dev/regression data, never into the frozen test.

### Coverage
- Vague memory: 8 dev / 6 test.
- Metadata filters: 6 dev / 4 test. Two are filter no-evidence cases
  (q15, t17): the topic exists in the library, but not under that domain.
- Multi-passage: 7 (dev q22–q24, test t10–t13).
- Cross-language: t03–t05 (Chinese queries, English articles).

### Gold labels
- `expected_item_ids` are `saved_items.id`. Hit@5/MRR are item-level.
- `supporting_passage` must appear in the item's `content_text` after removing whitespace.
- Audit (11/9) checks: file sha256, counts vs manifest, gold items exist and are
  chunked, passages found, gold items match their filters, no query in both splits.
- Rule for adding a gold item: the article's main topic answers the question and it
  contains a passage that actually answers it. A keyword match alone is not enough.
  Decided by reading the article, not by scores.

### Known biases
- All 20 test cases are Claude-drafted from titles/summaries. Their wording follows
  the article, so test is likely **easier** than real vague memories.
  Final-test scores may be optimistic.
- Find-style gold lists only the items I remembered; broad questions may have
  more correct items (see q24).
- `saved_day` uses UTC (t15 is an Oct 31 evening save labeled Nov 1).

### Label changes after freeze
- 2026-11-09, dev q24: added 8432857d6ae8a00d (Deploy WAR to AWS EC2).
  Details and old sha256 in `label_changes` in the manifest.
  Runs before 11/9 used the old q24 label.

## Storage choice

- Current dataset: 143 saved links, with 104 indexed into 2,206 chunks.
- Keep Chroma: it provides vector storage, metadata filtering, and local persistence with little setup. Query speed is acceptable for current use.
- Why not FAISS: FAISS supports saving and loading vector indexes, but metadata storage and mappings between vectors and documents would require additional management.
- Revisit this choice if query latency or memory usage becomes a problem as the dataset grows. Benchmark alternatives before deciding whether to switch.

## Metrics

All metrics run on the **dev split only** (30 cases). No LLM judge.

- **Hit@5:** for an answerable case, did any gold item appear in the top 5?
  Items are deduplicated first, so 5 chunks from one article count as 1 item.
- **MRR:** average of `1 / rank` of the first gold item, over the 24 answerable cases.
  Rank 1 = 1.0, rank 2 = 0.5, not found = 0.
- **No-evidence abstained:** for the 6 no-evidence cases, did search refuse?
  Rule: refuse when there is no result or the top-1 cosine distance is **> 0.6**.
- **Answerable wrongly refused:** answerable cases that were refused by the same rule.
- **Filter correct:** for the 6 filter cases, every returned item matches the
  domain/date filter. Checked against SQLite `saved_items`, not only the top 5.
- **Latency:** mean time per query, including the embedding API call.
- **Cost:** estimated tokens × price. Recorded in each `*_eval.run.json`.

Command: `python src/run_dev_eval.py --search dense|lexical|hybrid`
Each run saves per-question results (`.jsonl`) and a run record (`.run.json`:
config, corpus version, dataset sha256, git commit, elapsed time, cost).
Summary table: `python src/compare_dev.py` → `eval/dev-comparison.csv`.

## Manual Ask rubric

Used for the 10-case Ask audit (`src/run_ask_audit.py`). I rate each answer by hand.

- **relevant:** yes = answers the question. partial = on topic but incomplete. no = off topic or wrong.
- **citation_supported:** yes = every claim is in a cited excerpt. partial = some claims are not.
  no = the excerpts do not support the answer.
- Read the **full** excerpt before rating (see failure 6 below).
- Citation precision (too many or weak citations) is noted separately. It does not change the score.

## Results (dev, 2026-11-10)

Setup: corpus v2026-11-07 (105 indexed items, 2,216 chunks, `recursive_1000_50`),
`text-embedding-3-small`, top 5 items, threshold 0.6, q24 label after 11/9.
Code commit `bbb1d92`, results commit `4df9f2d`.

### Find (retrieval)

| Method  | Hit@5 | MRR   | No-evidence abstained | Answerable wrongly refused | Filter correct | Mean latency* |
|---------|-------|-------|-----------------------|----------------------------|----------------|---------------|
| lexical | 1.0   | 0.979 | **0/6**               | 0/24                       | 6/6            | 4 ms          |
| dense   | 1.0   | 0.958 | 5/6                   | 0/24                       | 6/6            | 457 ms        |
| hybrid  | 1.0   | 1.000 | 5/6                   | 0/24                       | 6/6            | 296 ms        |

Where they differ (all other answerable cases are rank 1 in all three):

| Case | Dense | Lexical | Hybrid |
|------|-------|---------|--------|
| q05 (vague, typo "ariticle")    | rank 2 | rank 1 | rank 1 |
| q24 (broad "deploy a web app")  | rank 2 | rank 1 | rank 1 |
| q27 (filter, "Python tutorial") | rank 1 | rank 2 | rank 1 |

Latency is mostly the embedding API call, and it changes a lot between runs.
On 11/7 dense was faster (285 ms vs 429 ms); on 11/10 hybrid was faster.
Hybrid only adds local work (FTS5 ~4 ms + RRF), so it cannot really be faster than dense.
Do not use these latency numbers to compare dense and hybrid.

Embedding cost per dev run: ~423 tokens (~$0.000008). Effectively free.

### Ask (answers, dense, gpt-4o, 10 dev cases)

| Relevant | Citation supported | Mean latency | Max latency | Input tokens / ask | Cost (10 asks) |
|----------|--------------------|--------------|-------------|--------------------|----------------|
| 10/10    | 10/10              | 1.8 s        | 3.1 s       | ~1.3k              | $0.040         |

Files: `eval/results/2026-11-10_dev_ask_audit.{jsonl,md}`.

## Development experiments (in order)

| Date | Change | Result | Kept? |
|------|--------|--------|-------|
| 11/4 | Lexical (SQLite FTS5) vs dense, same eval interface | Similar MRR. Lexical never abstains (0/6). | Both kept for comparison |
| 11/5 | Run records (config, commit, cost) | Rerun reproduced 11/4 exactly | Yes |
| 11/7 | Hybrid: RRF (k=60) over lexical + dense, dedup items first, abstain by dense distance | Best MRR | Kept as an option |
| 11/9 | Fixed q24 gold label (added the AWS WAR article) | Dense MRR 0.951 → 0.958 | Yes |
| 11/10 | Filter correctness checked for every returned item | 6/6 for all methods | Yes |
| 11/11 | Threshold 0.6 → 0.58 (one change, failure cluster: q17) | Fixed q17, but wrongly refused q10 | **No, keep 0.6** |

Details: `eval/results/2026-11-04_disagreements.md`, `2026-11-08_hybrid-failures.md`,
`2026-11-11_threshold-0.58.md`.

## Failure cases

### 1. q17: near-topic question with no answer is not refused
- Q: "How does QUIC's handshake work?" No saved item covers QUIC.
- Top results are DNS and UDP articles. Top distance 0.585 < 0.6, so search does not refuse.
- All three methods fail. The library has many networking articles, so the topic looks close.
- Lesson: distance tells "similar topic", not "has the answer".

### 2. q10 and q29: correct answers sit very close to the threshold
- q10 (Twilio events, answerable): 0.590. q29 ("the king who has lots of wives", answerable): 0.575.
- Both are rank 1, but a slightly different wording could push them over 0.6 and get refused.
- q10 is even farther than q17 (no evidence, 0.585). So **no threshold** can refuse q17 and keep q10.
  The 11/11 experiment confirmed this.

### 3. q24: broad question, gold label was incomplete
- Q: "How to deploy a web application?"
- Search returned "Deploy WAR to AWS EC2" at rank 1. It was not in the gold list, but it does answer the question.
- Fixed on 11/9 by reading the article (not by looking at scores). Recorded in `label_changes`.
- Lesson: for broad questions, gold lists only what I remembered. Some "misses" are label problems.

### 4. q05: vague question with a typo, dense ranks the right item 2nd
- Q: "There's an ariticle about the IOC using Factory design pattern."
- Dense rank 2; lexical and hybrid rank 1. Exact words ("Factory", "IOC") help here.
- This is the main case where hybrid beats dense.

### 5. Lexical never refuses
- Lexical abstained 0/6. FTS5 has no "distance", only a match score, and it almost always finds some keyword.
- So lexical alone cannot be used for Ask. Hybrid must keep the dense distance for refusal.

### 6. Evaluation bugs I found along the way
- **Audit sheet cut excerpts at 600 chars**, but the model saw ~1,000. I first rated q08/q09 as "no"
  and q07/q14 as "partial". After reading the full text, all were supported. Script fixed;
  original ratings kept in `human_notes`.
- **`/save` writes Chroma but not `chunks_fts`.** New saves are invisible to lexical/hybrid until
  FTS is rebuilt by hand. Must be fixed before shipping hybrid.
- `dense_abstain` crashed when dense returned nothing but lexical did. Fixed 11/7.
- `build_fts.py` never called `setup_fts()`. Fixed 11/7.

### Not a failure, but noted: citation precision
- q01 cites 3 excerpts for a one-line answer (the drama name). q07 [1] is weak for the main question.
- Answers are supported, but citations could be tighter.

## Selected configuration (2026-11-12)

**Decision: dense retrieval for v1. Threshold stays at 0.6.**

| Setting | Value |
|---------|-------|
| Retriever | dense (Chroma, cosine) |
| Embedding | `text-embedding-3-small` |
| Chunking | `recursive_1000_50` |
| Find | top 5 distinct items (from the top 30 chunks) |
| Ask context | top 5 chunks |
| Refuse rule | top-1 distance > 0.6, or the model returns empty `used_refs` |
| Answer model | gpt-4o, JSON mode |

Hybrid stays in the code (`--search hybrid`) as a candidate. It is not the default.

### Why dense
- **Lexical is out:** it never refuses (0/6). Ask would answer questions with no evidence.
- **Dense vs hybrid is a tie on what matters:** same Hit@5, same refusals, same filter results.
- **Hybrid's MRR lead is only 2 cases** (q05, q24: rank 2 → 1). The dev set is at the ceiling,
  so it cannot really tell the two apart.
- **Latency is not a reason either way** (see the note under Results).
- **Hybrid costs more to maintain:** `/save` must also update `chunks_fts`, and there is one more
  index to keep in sync.
- Rule from the plan: pick the simplest setup with good enough measured quality. Dense is simpler
  and already in production.

### Known limits
- 0 real-use questions. Most questions use words from the article, so they are easier than real
  vague memories. Real use may show bigger differences between methods.
- Only 6 no-evidence and 6 filter cases. One case = a big jump in the rate.
- Final test (20 cases) is not scored yet. It runs once in Sprint 4 with this configuration.

### When to revisit
After I collect real queries from self-use (they go into a dev/regression set, never the final test):
1. Rerun dense vs hybrid on dev + the new cases.
2. Switch to hybrid only if it fixes cases that dense gets wrong, and refusals do not get worse.
3. Before switching: make `/save` update `chunks_fts`, with a test.

The q17 problem (failure 1) is not fixed by either method. The planned fix is in the model layer
(backlog, after the trip): when the model says the context has no answer, `used_refs` must be empty.
