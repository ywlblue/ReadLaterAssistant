# Field notes

Real problems found while using the bot or running checks.
Only record what actually happened; do not make up activity.

## Bad results

| Date | What I did | Result | Why / notes |
|------|------------|--------|-------------|
| 2026-11-01 | baseline q05: "There's an ariticle about the IOC using Factory design pattern." | refused (model layer) | Retrieval same as 10/31 (distance 0.5278) and the expected article was in the context, but the model returned empty `used_refs`. Vague Find question in the Ask flow + no `temperature`. |
| 2026-11-01 | baseline run | crashed | Model returned `{}` in JSON mode. Fixed: retry once, then `layer = model_error`. |

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
