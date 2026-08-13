#!/usr/bin/env python3
"""Bake ~/nebula/tools.json for the Nebula app.

Reads  sheriffpicks.db (daily rows) + ~/nebula/categories.json (LLM categories)
Writes ~/nebula/tools.json  (per-tool app payload)
"""
import json, os, sqlite3, collections

HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HOME, "sheriffpicks/sheriffpicks.db")
CAT = os.path.join(HERE, "categories.json")
OUT = os.path.join(HERE, "tools.json")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
rows = conn.execute(
    "SELECT scrape_date, name, domain, url, color, pricing, source, source_score, sheriff_rank, tagline, reasoning "
    "FROM picks WHERE section='daily' ORDER BY scrape_date"
).fetchall()

# dedupe by (lower name, lower domain): latest row wins; aggregate across all —
# single pass: keep the latest row AND running aggregates together
agg = collections.OrderedDict()
latest_row = {}
for r in rows:
    key = (r["name"].strip().lower(), (r["domain"] or "").strip().lower())
    latest_row[key] = r
    a = agg.setdefault(key, {"appearances": 0, "sources": set(), "max_score": 0,
                             "best_rank": 99, "first": r["scrape_date"], "last": r["scrape_date"]})
    a["appearances"] += 1
    if r["source"]:
        a["sources"].add(r["source"])
    if r["source_score"] and r["source_score"] > a["max_score"]:
        a["max_score"] = r["source_score"]
    if r["sheriff_rank"] and r["sheriff_rank"] < a["best_rank"]:
        a["best_rank"] = r["sheriff_rank"]
    if r["scrape_date"] > a["last"]:
        a["last"] = r["scrape_date"]

cats = json.load(open(CAT))
out = []
for key, a in agg.items():
    latest = latest_row[key]
    cat = cats.get(latest["name"], {})
    out.append({
        "name": latest["name"],
        "domain": latest["domain"],
        "url": latest["url"],
        "color": latest["color"],
        "pricing": latest["pricing"],
        "sources": sorted(a["sources"]),
        "max_score": a["max_score"] or 0,
        "best_rank": None if a["best_rank"] == 99 else a["best_rank"],
        "first_seen": a["first"],
        "last_seen": a["last"],
        "appearances": a["appearances"],
        "tagline": latest["tagline"],
        "reasoning": latest["reasoning"],
        "category": cat.get("category", "Other"),
        "confidence": round(cat.get("confidence", 0), 2),
        "local_first": bool(cat.get("local_first", False)),
        "why": cat.get("why", ""),
    })

json.dump(out, open(OUT, "w"), indent=1)
print(f"wrote {OUT}: {len(out)} tools")
cnt = collections.Counter(t["category"] for t in out)
print("categories:", dict(cnt.most_common()))
print("local_first:", sum(1 for t in out if t["local_first"]))
print("multi-source:", sum(1 for t in out if len(t["sources"]) > 1))
