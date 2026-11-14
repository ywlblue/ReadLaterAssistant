# Field notes

Real problems found while using the bot or running checks.
Only record what actually happened; do not make up activity.

## Bad results

| Date | What I did | Result | Why / notes |
|------|------------|--------|-------------|
| 2026-11-01 | baseline q05: "There's an ariticle about the IOC using Factory design pattern." | refused (model layer) | Retrieval same as 10/31 (distance 0.5278) and the expected article was in the context, but the model returned empty `used_refs`. Vague Find question in the Ask flow + no `temperature`. |
| 2026-11-01 | baseline run | crashed | Model returned `{}` in JSON mode. Fixed: retry once, then `layer = model_error`. |
| 2026-11-13 | /find "What's that article I saved about a king?" (request d12329e1) | `hits: []` | Wanted Henry VIII (e8cd). All top-5 distances > 0.6, so Find abstained. Raw #1 was the wrong item. See case study below. |

## Failed saves

| Date | URL | Error | Wanted? |
|------|-----|-------|---------|
| 2026-10-19 | medium.com/... (Vault + AWS) <!-- TODO: full URL --> | http_403 | yes     |
| 2026-11-01 | hashicorp.com/resources/adopting-hashicorp-vault | http_429 (retry also blocked) | yes     |
| 2026-11-01 | blog.csdn.net/fuxuemingzhu/article/details/101900729 | human check (retry) | yes     |
| 2026-11-01 | javatpoint.com/dbms-boyce-codd-normal-form | link no longer valid | no      |
| 2026-11-01 | vegibit.com/node-js-blog-tutorial/ | link no longer valid | no      |
| 2026-11-01 | dongxiaoran.com/algo/basic/intro/ | link no longer valid | no      |

## Observations (not failures)

- 2026-11-01: refusal at the retrieval layer took 450 ms; answers took 2–3 s.
- 2026-11-01: sources repeat the same article ([1][2][5] all Dartmouth; DNS all Wikipedia).
- 2026-11-01: at least 8 of the 100 old bookmarks are dead
    (404 × 5 on 10/19, 3 more found on 11/1). Snapshots taken at save
    time keep the text even after the original link dies.
- 2026-11-02: need to run chunks.py and index.py manually when a new link is saved. Should add the chunking and indexing after saving successfully.
- 2026-11-13: 11 items are `fetched` but never digested (no `digest_json`), e.g. 31f6.
  They are indexed, so Find/Ask can return them, but `select_review` only picks
  `digested` items, so /review will never suggest them. TODO: run batch_digest on them.

## Case studies

### 2026-11-13 | Vague "king" query, and the Indian-democracy "hub" article

**What happened**

- `/find "What's that article I saved about a king?"` returned `hits: []`.
- The article I wanted exists and is indexed: `e8cd234919c4f656`,
  "Behind the Throne: Getting to know Henry VIII" (academytravel.com.au).

**Raw dense retrieval (no threshold, k=5 chunks)**

| Rank | Item | Distance |
|------|------|----------|
| 1 | 31f6 Indian democracy (New Yorker), wrong | 0.641 |
| 2 | e8cd Henry VIII, wanted | 0.645 |
| 3 | e8cd (another chunk) | 0.651 |
| 4-5 | 6cea Tutankhamun | 0.691 / 0.695 |

**Why it returned nothing**

- Every distance is above the selected threshold 0.6, so Find abstained as designed. Not a code bug.
- The query has one useful word ("king"). "What's that article I saved" adds nothing.
- Compare dev q29 "the king who has lots of wives": top 0.575, hit at rank 1.
- A looser threshold would not fix it: at 0.65 the **wrong** item ranks first (gap 0.004).

**Why 31f6 shows up so often**

- It appears in the top 5 of **7 of 30** dev queries (2026-11-11 dense run):
  q04 (rank 3), q12 (4), q16 (2, no-evidence case), q25 (1, its own question), q26 (2), q28 (4), q29 (2).
- All seven are humanities/politics questions.
- Likely reasons:
  1. **Small humanities pool.** The corpus is mostly technical tutorials and docs. Any non-technical query
     can only match a handful of articles (Egypt, Henry VIII, book reading, Indian democracy, US poll,
     documentary, K-drama), so the same few keep appearing.
  2. **Topic overlap, plus a literal king.** Government, leaders and power sit close to "king" in embedding
     space. The article also really mentions a king: Yadav tells an Indian fable about a king whose heart
     lived in a parrot ("king" x4, checked in `content_text`). That chunk is probably the 0.641 hit.
     The Henry VIII page ("king" x9) is a travel-company page about palaces and art, so its chunks are diluted.
  3. **Long document.** About 19k characters, so many chunks and more chances that one lands near a query
     (a "hub" document).
- Impact so far: no lost Hit@5 in dev (it ranks 2-4 except on its own question). It does add a near
  candidate to the no-evidence case q16, which matters for abstention.

**Not done / hypotheses to test later**

- Lexical/hybrid may help, but not for free: both articles contain "king" (Henry VIII x9, Indian x4).
  BM25 should favor Henry VIII (more hits, shorter page), but this is not checked. Use this query in the
  post-trip dense vs hybrid re-evaluation
  (real self-use query, dev/regression set only, never the final test).
- A larger, more varied corpus should reduce the hub effect. Re-check the 7/30 count after the trip.
- No threshold change for Find now: 0.6 is the evaluated M2 configuration, and this case shows
  loosening it would surface the wrong item first.

**Interview angle**

- Vague-memory queries: when one word carries all the meaning, dense retrieval cannot separate nearby topics.
- The threshold did its job: it refused instead of confidently returning the wrong article.
- Hub documents in a small, skewed personal corpus: a real effect seen in my own data, not a textbook example.
