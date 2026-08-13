#!/usr/bin/env python3
"""Generate ~/nebula/app.json — compact payload for the Nebula app.

From tools.json: categories + per-tool compact row:
  [name, color, score, best_rank, source_idx, first_seen, cat_idx, local_first, tagline, url]
"""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
tools = json.load(open(os.path.join(HERE, "tools.json")))

cats = ["Games", "Art / creative", "Dev tools", "Social / fun", "AI / ML", "Productivity",
        "Retro / nostalgia", "Maps / geo", "Education / learning", "Other", "Science / space",
        "Finance", "Audio / music", "Health", "Security", "Data-viz", "Local-first / privacy"]
cat_idx = {c: i for i, c in enumerate(cats)}
srcs = ["HN", "Reddit", "X"]
src_idx = {"Hacker News": 0, "Reddit": 1, "X": 2}

dates = sorted({t["first_seen"] for t in tools})
date_idx = {d: i for i, d in enumerate(dates)}

rows = []
remapped = collections.Counter()
for t in tools:
    c = t["category"]
    if c not in cat_idx:
        # never silently drop a tool: unknown LLM labels land in Other
        remapped[c] += 1
        c = "Other"
    s = t["sources"][0] if t["sources"] else ""
    rows.append([
        t["name"],
        t["color"] or "#9aa4b2",
        t["max_score"] or 0,
        t["best_rank"],
        src_idx.get(s, -1),
        date_idx[t["first_seen"]],
        cat_idx[c],
        1 if t["local_first"] else 0,
        t["tagline"] or "",
        t["url"] or "",
    ])

payload = {
    "categories": cats,
    "sources": srcs,
    "dates": dates,
    "tools": rows,
}
out = os.path.join(HERE, "app.json")
json.dump(payload, open(out, "w"), separators=(",", ":"))
print(f"wrote {out}: {len(rows)} tools, {len(dates)} days, remapped-to-Other: {dict(remapped)}")
