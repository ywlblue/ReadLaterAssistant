# Workflow design

Status (11/15): review selection, `/review` and `/opened`, the LLM reason, command
routing, typed tools, timeouts and the 20 offline workflow cases are done.
Left for M3: spot-check 3 review reasons against their summaries.

## Review: what to resurface

Code: `select_review` in `readlater/review.py`.

1. Pool = the 30 newest `digested` items (`saved_at DESC, id`).
2. Drop items I marked as opened.
3. Drop items suggested in the last 14 days.
4. Return up to 3 of what's left, **oldest first**.

Why these choices:
- **Oldest first.** Items near the edge of the 30-item window get a turn before
  they drop out. With newest first, the latest saves would keep winning.
- **Pool first, then filter.** "30 most recent" means my 30 latest saves, not the
  30 latest eligible ones. Downside: if I've opened or been shown all of them,
  review returns nothing even though older unread items exist. Fine for v1. An
  empty result is honest. Revisit if it shows up in self-use.
- **Only `digested`.** The reason line needs a stored summary to work from.
  Failed or half-processed items have nothing to ground it.
- **`id` as tie-break.** Same data always gives the same picks.

## Data

| Table | Row means |
|---|---|
| `item_opens(item_id, opened_at)` | I said I opened it (`/opened`). Self-report, not proof I read it. |
| `review_recommendations(request_id, item_id, recommended_at)` | One row per suggested item. |

Both live in the same SQLite file as `saved_items`, so they survive restarts.

This is business history: it tells review what was already suggested. It is
**not** an execution checkpoint. Nothing here resumes a half-finished run.

## Where plain code is enough

- Picking items is one SQL query. No model call, so no cost, no timeout and the
  same input always gives the same output. Easy to test.
- The LLM will only write the one-line reason, from the stored digest.
- If the reason call fails, review still returns the pick with a fallback reason
  built from the stored summary (`review_reason` in `readlater/review.py`, case W19).

## Time handling

- `now` is a parameter, not read inside the function, so tests can fake "15 days ago".
- Timestamps are UTC ISO strings, compared as strings. Every write must use
  `datetime.now(timezone.utc)`, or the comparison breaks.

## Tests

`tests/test_review.py`, 10 cases, all passing:

- Empty DB → `[]`
- Opened, `digest_failed` and `fetched` items are never picked
- 32 items → the 2 oldest are outside the pool and never picked
- Suggested 13 days ago → skipped; 15 days ago → allowed again
- Record, close, reopen → the next 3 items, no overlap (restart check)
- Same data twice → same result
- `record_review(conn, "r", "abc", now)` → `TypeError`
- `record_opened` with an unknown ID → `ValueError`

Two mistakes worth remembering:
- Passing a string to `record_review` stored `'a'`, `'b'`, `'c'` as three item
  IDs. A Python `str` is iterable and type hints aren't checked at runtime. Now it
  raises instead.
- The first restart test had no data. Empty vs empty has no overlap, so it passed
  without testing anything. Assert the input isn't empty before asserting "no overlap".

## Known gaps

- Opening the same item twice adds two rows. Harmless for selection.

## Timeouts and retries

Every external call has a timeout. Only malformed model output is retried, once.

| Call | Timeout | Retries | Where |
|---|---|---|---|
| Fetch a page | 10 s | 0 | `fetch.py` |
| LLM (digest, answer, review reason) | 25 s | 0 network retries | `model.py` |
| Embedding | 15 s | 1 | `embeddings.py` |
| Bot → API | 120 s | 0 | `bot.py` |
| Telegram `getUpdates` / `sendMessage` | 40 s / 30 s | 0 | `bot.py` |

- Before 11/15 the OpenAI SDK used its default: 600 s plus 2 silent retries.
  That is longer than the bot's 120 s wait, so the bot gave up first.
- Worst cases now stay under 120 s: `/review` = 3 reasons x 25 s = 75 s;
  `/ask` = 2 model tries x 25 s + 2 x 15 s embedding = 80 s.
- Malformed output = bad JSON, wrong schema, or (for Ask) a source ref that was not
  in the context. It gets one retry, then a controlled error.
- A timeout is not retried. Retrying a slow model just doubles the wait.

What the user sees when something fails:

| Failure | Reply | Data |
|---|---|---|
| Digest timeout / bad JSON / provider error | `Error: <reason>` + "Send the same url again to retry." | Item and fetched text are kept (`digest_failed`) |
| Ask: model timeout | "The model did not respond in time." | Event recorded |
| Ask: bad output twice | "The model returned an invalid response." No sources shown. | Event recorded |
| Find/Ask: embedding or Chroma error | "Search is not available right now." | Ask event recorded; Find returns 503 |
| Review: reason call fails | Fallback reason from the stored summary | Picks still recorded |
| Bot → API timeout / API down | "The server took too long to reply." / "Cannot reach the server." | Nothing recorded |
| Any other non-200 from the API | `Error: <detail>` | — |

## Offline workflow cases

- Cases: `eval/workflow-cases.jsonl` (20). Runner: `python -m readlater.evals.eval_workflow`.
  Results: `eval/workflow-results.json`. 11/15: 20/20 pass.
- Each message goes through the same path as the real bot:
  `bot.dispatch(text)` → `route()` → bot handler → FastAPI (`TestClient`) → storage / model.
- Nothing leaves the machine: SQLite is a temp file per case, Chroma is in memory,
  and the model, page fetch and embedding are fakes chosen by the case.
- Chunk distances are fixed: "near" ≈ 0, "far" ≈ 0.71 (threshold 0.6).
- Every case also checks: no `Encounter an error` in any reply (no unhandled
  exception), DB row counts, and how many times the fake model was called.

| ID | Type | What it tests | Send → expect | Model calls |
|---|---|---|---|---|
| W06 | valid | Save works; same URL twice = one item | URL → `Saved:`, `Summary:`; again → `Saved:` | 1 |
| W11 | valid | Ask with a citation, then feedback | `/ask` → answer + `[1] <url>` + `Request ID`; `/found <id>` → `Recorded` | 1 |
| W16 | valid | Find order + "Weaker matches" label, then feedback | `/find` → `1. Load balancing`, `Weaker matches:` `2. Caching basics`; `/missed <id>` → `Recorded` | 0 |
| W07 | fetch failure | 404 is visible and recorded | URL → `Fetch failure: http_404` | 0 |
| W04 | model failure | Digest bad JSON twice → one retry, then error | URL → `Send the same url again to retry`; text kept | 2 |
| W08 | model failure | Bad JSON once, then good → retry fixes it | URL → `Saved:`, `Summary:` | 2 |
| W10 | model failure | Provider error is not an HTTP 500 | URL → `Error: model_error`; text kept | 1 |
| W13 | model failure | Ask bad JSON twice | `/ask` → `The model returned an invalid response.`, no sources | 2 |
| W14 | model failure | Ask cites ref `[9]` that does not exist | `/ask` → invalid response; made-up answer not shown | 2 |
| W09 | timeout | Digest timeout, no retry | URL → `Error: llm_timeout`; text kept | 1 |
| W12 | timeout | Ask model timeout | `/ask` → `did not respond in time`, no sources | 1 |
| W20 | timeout | Bot → API timeout | `/review`, `/ask` → `The server took too long to reply` | 0 |
| W17 | tool failure | Embedding timeout in Find and Ask | `/find` → `Error: Search is not available right now.`; `/ask` → same text | 0 |
| W03 | missing evidence | Empty index → abstain | `/ask` → `No saved item has enough evidence` | 0 |
| W15 | missing evidence | Best chunk over 0.6 → abstain | `/ask` → `No saved item has enough evidence` | 0 |
| W02 | invalid args | `/opened` with unknown ID | → `Item ID not found`; no row | 0 |
| W05 | unsupported input | Plain text is not saved | `hello there` → `Commands:` | 0 |
| W18 | invalid args | Missing arg, unknown request ID, URL with no host | `/find` → `Commands:`; `/found x` → `ID not found`; `https://` → `Error: Invalid URL` | 0 |
| W01 | repeated review | First review picks 2, second is empty | `/review` → both titles + `Why:`; again → `Nothing to review` | 2 |
| W19 | repeated review | Skip opened + picked 2 days ago; allow picked 20 days ago; fallback reason | `/review` → `1. Old pick`, `2. Never picked`, `Why: Saved on…` | 2 |

Coverage vs the M3 check:

| M3 asks for | Cases |
|---|---|
| Valid commands | W06, W11, W16 |
| Invalid args | W02, W05, W18 |
| Missing evidence | W03, W15 |
| Empty backlog | W01 (step 2) |
| Repeated review | W01, W19 |
| Model / tool failure | W04, W07, W08, W10, W13, W14, W17, W19 |
| Timeouts | W09, W12, W17, W20 |

Bugs these cases found (fixed 11/15):
- Digest had no malformed-output retry, although M0 asked for one.
- A provider error during digest became HTTP 500, and the bot showed a pydantic
  error. Now it is `model_error` and the fetched text is kept.
- An unknown source ref in Ask raised `ValueError` → HTTP 500. Now it counts as
  malformed output.
- An embedding failure in Find/Ask became HTTP 500. Now it is a short message.
- The bot parsed error bodies as normal responses. Now any non-200 becomes `Error: <detail>`.
- Check: the new cases W04, W08, W10, W12, W14 and W17 all fail on the old code (`e1c4c40`).

Gaps in these cases:
- New saves skip chunking/indexing in these cases (`process_document` and
  `build_index` are mocked). Indexing has its own tests in `tests/test_save_index.py`.
- The fake model is chosen per case, so one case cannot mix "timeout, then OK".
