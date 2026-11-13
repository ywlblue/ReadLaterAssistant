# Workflow design

Status (11/12): review selection is done and tested. Not built yet: `/review` and
`/opened` in the bot, the LLM reason, command routing, typed tools, timeouts and
the 20 workflow cases.

## Review: what to resurface

Code: `select_review` in `src/review.py`.

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
- Plan (not built): if the reason call fails, still return title + link.

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
