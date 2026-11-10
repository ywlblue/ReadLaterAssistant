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