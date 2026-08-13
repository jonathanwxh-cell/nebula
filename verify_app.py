#!/usr/bin/env python3
"""Smoke test for the Nebula app payload. Run after pipeline.py; exit 0 = pass.

Checks app.json schema and consistency with tools.json — catches regressions
like gen_app.py's hardcoded category list drifting from classify.py's taxonomy,
truncated rows, or out-of-range indices that would silently break the canvas app.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []

def check(cond, msg):
    if not cond:
        fails.append(msg)

app = json.load(open(os.path.join(HERE, "app.json")))
tools = json.load(open(os.path.join(HERE, "tools.json")))

cats = app["categories"]
srcs = app["sources"]
dates = app["dates"]
rows = app["tools"]

check(len(cats) >= 10, f"too few categories: {len(cats)}")
check(dates == sorted(dates), "dates not sorted")
check(len(dates) >= 1, "no dates")
check(len(rows) == len(tools), f"app.json has {len(rows)} tools but tools.json has {len(tools)}")

HEX = re.compile(r"^#[0-9a-fA-F]{3,8}$")
bad_row = bad_src = bad_date = bad_cat = bad_color = 0
for r in rows:
    if len(r) != 10:
        bad_row += 1
        continue
    if not (0 <= r[4] < len(srcs)):
        bad_src += 1
    if not (0 <= r[5] < len(dates)):
        bad_date += 1
    if not (0 <= r[6] < len(cats)):
        bad_cat += 1
    if not HEX.match(r[1] or ""):
        bad_color += 1
check(bad_row == 0, f"{bad_row} rows with wrong length (expect 10)")
check(bad_src == 0, f"{bad_src} rows with out-of-range source index")
check(bad_date == 0, f"{bad_date} rows with out-of-range date index")
check(bad_cat == 0, f"{bad_cat} rows with out-of-range category index")
check(bad_color == 0, f"{bad_color} rows with non-hex color")

# every category in tools.json must exist in the app payload list
payload_cats = set(cats)
missing = {t["category"] for t in tools} - payload_cats
check(not missing, f"categories in tools.json missing from payload: {missing}")

# every payload category must be reachable (no empty constellation by construction)
used = {r[6] for r in rows}
empty = [cats[i] for i in range(len(cats)) if i not in used]
if empty:
    print(f"note: empty constellations: {empty}")

if fails:
    print("SMOKE TEST FAILED:")
    for f in fails:
        print(" -", f)
    sys.exit(1)
print(f"smoke OK: {len(rows)} tools, {len(cats)} categories, {len(dates)} days")
