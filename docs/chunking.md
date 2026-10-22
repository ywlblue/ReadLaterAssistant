# Chunking

Code: `src/chunks.py`. Table: `chunks`. No embeddings here; Friday's index reads chunks from this table.

## Strategy

- **Splitter:** LangChain `RecursiveCharacterTextSplitter`
- **Separators:** `"\n\n"`, `"\n"`, `"。"`, `". "`, `"！"`, `"？"`, `" "`, `""`
- **Size:** `chunk_size=1000` characters, `chunk_overlap=50`
- **Strategy name:** `recursive_1000_50` (stored in `chunks.strategy`)

Why this one:

- One strategy is enough for M1. LangChain is already used in the repo, so no new dependency.
- Fetched `content_text` is mostly one line per HTML element. The splitter almost always cuts at `"\n"`, so chunks rarely end in the middle of a sentence.
- 1000 characters holds about one Q&A pair or one short section on the pages checked below.

## Chunk ID

```
sha256(f"{item_id}:{strategy}:{chunk_index}:{content_sha256}")
```

- Same snapshot + same strategy → same ID, so re-runs insert nothing new (`INSERT OR IGNORE`).
- Changed content (`content_sha256`) or changed strategy → new IDs, so old chunks are never silently kept for new parameters.
- `UNIQUE(item_id, chunk_index, strategy)` is a second guard.

## Re-run check (Oct 22)

Ran `python src/chunks.py` twice on 5 items. Both runs: 112 chunks, same count per item. No duplicate chunk text within an item. Chunk length 348–999.

| Item | Page type | Chars | Chunks |
|---|---|---|---|
| `1e122840bf42ea63` JDBC interview questions | long Q&A | 23,982 | 27 |
| `2431fbb46605e2f9` objectdb JPA delete | structured, code | 7,110 | 8 |
| `8d3838e130953273` Java EE tutorial contents | table of contents | 66,278 | 70 |
| `b6b726c7e072489e` Crafting Interpreters contents | short, table of contents | 1,401 | 2 |
| `ce6513377c2b650f` Java tutorial for beginners | nav + short article | 4,275 | 5 |

## What 10 chunks showed

1. **Q&A page works well** (`1e12…` #3, #4). Each chunk holds 2–4 whole questions with answers.
2. **Overlap 50 is about one short line.** At the `1e12…` #3/#4 boundary, only the label `ResultSet.TYPE_SCROLL_SENSITIVE` is carried over; its description starts the next chunk. Label and meaning still end up together in #4, so this is acceptable. 16 of 26 boundaries on that page share text.
3. **objectdb page text is broken before chunking** (`2431…` #2, #3). Every Java name is followed by its hover tooltip (full class name + description), and code is one token per line (`class` / `Employee` / `{`). Chunking cannot fix this; it is a fetch/extraction problem.
4. **Table-of-contents pages make many useless chunks.** `8d38…` is 70 chunks of headings only (#0, #40); `b6b7…` is 2. They contain many keywords but no answers. This explains why the Java EE contents page ranked first in the Oct 21 QA spike.
5. **Navigation menus become chunks too** (`ce65…` #1 is a sidebar list). The real article is in #3–#4.
6. **Short last chunks are fine.** `b6b7…` #1 is 451 chars and `ce65…` #4 is 615 chars; both are readable on their own.

## Decision

Keep `recursive_1000_50` for M1. Re-check after Friday's 10 Find queries; if answers miss text at chunk edges, try `recursive_1000_150` as the second strategy.

## Known limitations

- **Stale chunks:** when an item's content changes, new chunks are added but the old ones stay. Delete by `item_id` before re-chunking; handle before building the index.
- **Separators are not in the strategy name.** Changing them without renaming the strategy would keep old chunks. Rename the strategy whenever separators change.
- **Table-of-contents and nav-only pages** are indexed like articles. Possible later fix: skip or down-rank them.
- **objectdb tooltip text** pollutes chunks. Fix belongs in `fetch.py`, not here.
- **Only 5 items chunked so far.** M1 needs at least 50 indexed pages.
- SQLite does not enforce `REFERENCES saved_items(id)` unless `PRAGMA foreign_keys = ON`.
