#!/usr/bin/env python3
"""Nebula pipeline: sheriffpicks.db -> categories.json -> tools.json -> app.json.

Run after scrape.py adds a new day. Each step is idempotent and incremental
(classify only calls the LLM for tools not already in the cache).
Safe to re-run at any time: regenerating app.json from unchanged data is a no-op
in content terms.
"""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("classify new tools (LLM, incremental)", "classify.py"),
    ("aggregate tools.json", "build_json.py"),
    ("bake app.json payload", "gen_app.py"),
]

def main():
    t0 = time.time()
    for label, script in STEPS:
        print(f"\n== {label} ==")
        r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                           cwd=HERE, capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            sys.exit(f"STEP FAILED: {script} (exit {r.returncode})")
    app = os.path.join(HERE, "app.json")
    size = os.path.getsize(app)
    print(f"\npipeline OK in {time.time()-t0:.1f}s — app.json {size/1024:.0f} KB")

if __name__ == "__main__":
    main()
