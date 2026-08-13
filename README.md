# NEBULA

552 hand-picked tools from [sheriffpicks](../sheriffpicks), rendered as one living sky.

Every tool the Sheriff has picked (2026-07-04 → today) becomes a star: its real brand
color, sized by virality, grouped into constellations by what the tool *is*. Scrub the
timeline and the sky ignites day by day. Amber rings mark what's rising right now;
dashed rings mark gaps — categories where demand outruns supply.

## Run

```bash
cd nebula && python3 -m http.server 8792
# open http://localhost:8792/index.html
```

Zero dependencies: one `<canvas>`, one `app.json`, no build step.

## Interactions

- **drag** pan · **scroll** zoom · **RESET** recentre
- **click a constellation** → drill in (top-8 stars labeled on an outer ring, full list in the panel)
- **click empty space** → back to the whole sky
- **timeline / ▶** → replay the 37 days; the panel stays in sync
- **search** → dim everything else, amber-ring the matches, Enter jumps to the first match

## Data

| Field | Becomes |
|---|---|
| `color` (brand hex, from the pick) | star color |
| `source_score` (virality) | star size/brightness |
| category (LLM-mined from tagline+reasoning) | constellation |
| `scrape_date` | timeline (the sky grows day by day) |
| rising = last-7d rate > 1.2× prior-14d rate | solid amber ring ▲ |
| gap = high avg score + low count | dashed amber ring |

## Pipeline (auto-grow)

```bash
python3 pipeline.py
```

Runs `classify.py` (incremental LLM categorization, cached by `name|domain` in
`classify_cache.jsonl`) → `build_json.py` (aggregates per-tool stats from
`../sheriffpicks/sheriffpicks.db`) → `gen_app.py` (bakes the compact `app.json`).
Idempotent; safe to run after every daily scrape.

## Files

- `index.html` — the whole app (single file, Canvas 2D, no framework)
- `app.json` — baked runtime payload (committed so the static site works standalone)
- `pipeline.py` — one-command rebuild
- `classify.py` — LLM categorization (DeepSeek `deepseek-chat`; incremental cache)
- `build_json.py` — per-tool aggregation from the SQLite picks DB
- `gen_app.py` — compact payload generator
- `categories.json`, `tools.json` — pipeline intermediates
