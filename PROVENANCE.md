# PROVENANCE — Nebula

## 2026-08-13 — Phase 1 initial release

**Scope:** new project. Single-file canvas app (`index.html`), LLM categorization
pipeline (`classify.py`), aggregation (`build_json.py`), payload baker (`gen_app.py`),
one-command runner (`pipeline.py`), baked data (`app.json`, `tools.json`, `categories.json`).

**Source data:** `~/sheriffpicks/sheriffpicks.db` (661-row cleaned state, 554 daily
picks across 37 days, 2026-07-04 → 2026-08-13). No schema or data changes made to
the source DB — the pipeline is read-only against it.

**Build verification (Hermes, this box):**
- `python3 -m py_compile classify.py build_json.py gen_app.py pipeline.py` → OK
- `python3 pipeline.py` end-to-end → OK (full pass 128–145s; incremental re-run 0.3s on cache hit)
- Headless render QA (Playwright + vision): constellation overview, drill-in
  (large cluster = Games 130, small cluster = Security 10), timeline scrub
  (day 1 → 15 tools, day 11 → 164, day 37 → 552), panel-sync on scrub,
  empty-space click deselect, search dim/highlight, zoom, pan. Console: 0 errors, 0 warnings.
- LLM categorization: 552 tools, 17 categories, hand-checked sample of 50 rows
  (~48 sensible). Run-to-run LLM drift observed (Other: 22 → 113 across identical
  prompts); mitigated with a deterministic regex rescue pass applied only to
  LLM-`Other` tools (35 rescued; Other locked at 30 = 5.4%).
- Known data quirk: `categories.json` is keyed by tool name; 2 same-name tools
  (different domains) collapse into one entry (552 tools → 550 entries). Both
  inherit the same category. Harmless at this scale; documented in README.

**Static security scan (added lines):** no hardcoded secrets, no `shell=True`,
no `eval`/`exec`, no f-string SQL, no `pickle`. `classify.py` reads
`DEEPSEEK_API_KEY` from `~/.hermes/profiles/dev/.env` and never prints it.
`index.html` escapes all tool-derived strings before `innerHTML` (`escapeHtml`).

**Independent review (fresh-context subagent, fail-closed JSON):**
- VERDICT: initial FAIL → all findings resolved. 2 real security fixes (unescaped tool
  color in innerHTML style attr → `safeColor`; raw error object in fetch catch →
  textContent), 1 verified false positive (claimed JS syntax error was display-layer
  digit masking; on-disk bytes confirmed correct via `od -c` + `node --check`),
  9 robustness suggestions adopted. Full record: reviews/deepseek-initial-20260813.md.

**DeepSeek release sign-off #1 (claude -p --model sonnet, read-only, $1.33):**
- VERDICT: APPROVED, zero blockers. Model confirmed `deepseek-v4-flash` via modelUsage.
- Independently re-derived all verify_app.py assertions and cross-checked every data
  claim (552 rows, day 1/11/37 counts, distribution, URL schemes, dup-name collapse).
- One non-blocking fix taken after approval (`escapeHtml` + `'`), which invalidated
  sign-off #1 per protocol → sign-off #2 rerun over the final state below.

**DeepSeek release sign-off #2 (final state, claude -p --model sonnet, read-only, $0.91):**
- VERDICT: APPROVED, zero blockers. Model confirmed `deepseek-v4-flash` via modelUsage.
- Byte-verified the `escapeHtml` `'` fix (od -c), audited all innerHTML sinks,
  re-derived payload anchors independently (552 rows = 544 https + 8 http, 37 dates,
  categories.json 550 keys, zero javascript:/data: schemes, secret sweep clean).
- Recommendation: commit with docs, then deploy. Full record: reviews/deepseek-initial-20260813.md.

**Deploy:**
- GitHub: `jonathanwxh-cell/nebula` (public), initial commit `c6200e9`, local HEAD ==
  remote master (verified via `gh api`).
- Vercel: production deploy live at https://nebula-mu-three.vercel.app (CLI,
  account jonathanwxh-3970 / team jons-projects-0e19e128). Live render verified
  via headless browser: full galaxy, signals, chrome; console clean except a
  favicon 404 (fixed by the inline-SVG favicon in the follow-up cosmetic commit).
- Custom domain: `nebula.alyoechosys.dev` added to the Vercel project; CNAME created
  at Cloudflare via API (`nebula → eb4acf9bed2f3f01.vercel-dns-017.com`, DNS-only,
  record id 764c1418fa1dbb5cbd146d5d4e64776a, zone 61b02da8bf372ff56fd5ba14a34c9d28).
  Vercel domain verification: passed. HTTPS live and render-verified
  (full galaxy, 0 console errors). Cloudflare token stored as CLOUDFLARE_API_TOKEN
  in the dev profile .env (zone-scoped; /user/tokens/verify rejects it but zone
  endpoints work — a known scoped-token quirk).
- Post-sign-off cosmetic change: inline SVG favicon `<link>` added to `<head>`
  (static markup only — no logic touched; sign-offs #1/#2 cover all executable code).
