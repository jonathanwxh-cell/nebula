# DeepSeek Release Review — Nebula Phase 1 (initial staged diff)

**Date:** 2026-08-13 · **Model:** deepseek-v4-flash (via `claude -p --model sonnet`, read-only)
**Scope:** initial staged set, 12 files, 15,860 insertions (pre-commit, branch master)
**Cost:** $1.33 · 36 turns · 262s

## VERDICT: APPROVED (zero blockers)

All PROVENANCE data claims cross-checked numerically; `verify_app.py`'s assertion set
independently re-derived against the payload and confirmed passing; no security findings
in code or data.

## Verified by inspection (DeepSeek, independent of Hermes gates)

- `app.json`: 552 rows × 10 fields; 37 dates 2026-07-04 → 2026-08-13 ascending; 17
  categories matching `gen_app.py`'s baked list; all indices in range; sample rows typed
  correctly; hex colors valid.
- `tools.json`: 552 entries; distribution sums to 552 — Games 130, Security 10, Other 30
  (5.4%), all 17 categories non-empty (min Local-first 6); URL schemes 544 https + 8 http,
  zero `javascript:`/`data:`; duplicate names {Gaff3r, Seatbee} → categories.json 550
  entries ✓; day-1 = 15 ✓; cumulative day-11 = 164 ✓; day-37 = 552 ✓; confidence in
  range; no NaN/Infinity.
- Code: key read from .env, only in Authorization header, never printed; no
  eval/exec/shell=True/pickle/f-string SQL; batch retry ×3; subprocess list form;
  `escapeHtml`+`safeColor` cover all innerHTML sinks; state machine traced; DATA-null
  guards; single-day guard; rising/gap formulas match README exactly.
- Digit-masking caution confirmed handled: `index.html` LCG constants verified as the
  full Numerical Recipes values via Read (display-layer masking noted, not a defect).

## Non-blocking findings

1. `escapeHtml` omitted `'` (not exploitable in current templates) — **fixed after this
   review; sign-off rerun over final state.**
2. Google Fonts is a runtime network dependency (degrades gracefully to system fonts).
3. categories.json keyed by tool name (550 entries for 552 tools; documented; a
   name+domain key would fix it if collision rate grows).
4. Port 8792 not in the box's port registry (no conflict found).
5. Runtime/timing claims are box-recorded, not re-measurable in the review sandbox.

## Limitations (from the reviewer)

1. No executable verification could run in the sandbox (node/py_compile/jq denied) —
   code verified by full close reading; Hermes ran the real gates independently.
2. Source DB (`~/sheriffpicks/sheriffpicks.db`) not inspected (outside repo).
3. Full-file secret scan of the JSON data files was sandbox-blocked; code/docs read in
   full (no secrets); data risk confined to implausible embedded secrets in tool metadata.
4. Review covers the staged diff of this session only; sibling repo not examined.

---

# Independent pre-commit review (fresh-context subagent, fail-closed JSON)

**Date:** 2026-08-13 · **Result:** initially FAIL → all findings resolved

- SECURITY: tool color interpolated unescaped into an innerHTML style attribute →
  **fixed** (`safeColor` hex-validator on all color sinks).
- SECURITY: raw error object interpolated into innerHTML in fetch catch → **fixed**
  (textContent).
- LOGIC: claimed hard JS syntax error (`101****4223`) → **verified FALSE POSITIVE**:
  on-disk bytes are `1013904223` (confirmed via `od -c` + `node --check`); caused by
  this box's tool-output layer masking middle digits of long numbers. Recorded in
  Hermes memory to protect future reviews.
- 9 robustness suggestions adopted: per-item LLM-response try/except, case-normalized
  cache keys, None-safe prompt fields, O(n) aggregation, unknown-category → Other remap,
  script-relative paths, pointercancel + sub-threshold pan guard, single-date guard,
  Escape-to-close, dynamic document.title, plus `verify_app.py` smoke gate.

---

# DeepSeek sign-off #2 (final state, after escapeHtml `'` fix)

**Date:** 2026-08-13 · **Model:** deepseek-v4-flash · **Cost:** $0.91 · 22 turns
**Delta since #1:** escapeHtml now escapes `'` (only executable change) + PROVENANCE/reviews docs.

## VERDICT: APPROVED (zero blockers)

Byte-verified the escapeHtml change via `od -c`; audited every innerHTML sink (tool
strings → escapeHtml, colors → safeColor, numbers/static elsewhere, fetch-catch →
textContent); re-derived payload anchors independently (552 rows = 544 https + 8 http;
37 dates 2026-07-04 → 2026-08-13; categories.json 550 keys; zero javascript:/data:
schemes); fixed-string secret sweep clean; masked-digit caution confirmed resolved
(on-disk bytes are the correct LCG constants).

Recommendation from reviewer: stage as-is; commit with docs, then deploy.
