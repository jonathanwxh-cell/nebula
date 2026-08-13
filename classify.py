#!/usr/bin/env python3
"""Classify sheriffpicks tools into categories via DeepSeek API (batched, incremental cache).

Reads  ../sheriffpicks/sheriffpicks.db     (daily rows, deduped by lower(name)+domain, latest wins)
Writes ~/nebula/categories.json            (name -> {category, confidence, local_first, why})
Cache  ~/nebula/classify_cache.jsonl       (keyed by "name|domain" — stable across new days)

DeepSeek API key is read from ~/.hermes/profiles/dev/.env (never printed).
The model 'deepseek-chat' is used: 'deepseek-v4-flash' burns its token budget on
reasoning_content before emitting content, which breaks JSON extraction.
"""
import json, os, re, sqlite3, sys, time, urllib.request

HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HOME, "sheriffpicks/sheriffpicks.db")
CACHE = os.path.join(HERE, "classify_cache.jsonl")
OUT = os.path.join(HERE, "categories.json")
BASE = "https://api.deepseek.com"
MODEL = "deepseek-chat"
BATCH = 20

CATEGORIES = [
    "Games", "Dev tools", "AI / ML", "Art / creative", "Maps / geo", "Local-first / privacy",
    "Retro / nostalgia", "Data-viz", "Science / space", "Education / learning", "Audio / music",
    "Finance", "Health", "Productivity", "Social / fun", "Security", "Other",
]

def load_key():
    for line in open(os.path.join(HOME, ".hermes/profiles/dev/.env")):
        line = line.strip()
        if line.startswith("DEEPSEEK_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("DEEPSEEK_API_KEY not found in ~/.hermes/profiles/dev/.env")

def load_tools():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """SELECT scrape_date, name, domain, url, color, pricing, source,
                  source_score, sheriff_rank, tagline, reasoning
           FROM picks WHERE section='daily' ORDER BY scrape_date"""
    ).fetchall()
    con.close()
    groups = {}
    for r in rows:
        d = dict(r)
        groups[(d["name"].strip().lower(), (d["domain"] or "").strip().lower())] = d
    return list(groups.values())

def call_api(key, batch):
    items = "\n".join(
        f'{i}. name: {t[1]!r} | tagline: {t[2]!r} | why-picked: {t[3]!r}' for i, t in enumerate(batch)
    )
    cats = " / ".join(CATEGORIES)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": (
                "You classify small web tools/projects into exactly one category. "
                f"Categories: {cats}. Pick the most salient one. "
                "Also flag local_first=true if the tagline/why emphasizes local/offline/no-server/no-account/in-browser/no-upload. "
                "Respond with ONLY a JSON object mapping the item index (as string) to "
                '{"category": "...", "confidence": 0-1, "local_first": true/false, "why": "max 6 words"}. '
                "The category MUST be copied exactly from the list."
            )},
            {"role": "user", "content": items},
        ],
        "temperature": 0,
        "max_tokens": 2500,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=150) as r:
        body = json.loads(r.read().decode())
    return body["choices"][0]["message"]["content"]

def extract_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in response: {text[:200]}")
    return json.loads(text[start:end + 1])

# Deterministic rescue pass: applied ONLY to tools the LLM left in "Other".
# Conservative, high-precision rules — order matters, first match wins.
RESCUE = [
    (r"\b(drum|synth|audio|music|sound|guitar|piano|chord)\b", "Audio / music"),
    (r"\b(game|puzzle|arcade|rpg|doom|chess|wordle|platformer)\b", "Games"),
    (r"\b(retro|vintage|nostalgia|90s|80s|dos|emulator|crt|dial.?up)\b", "Retro / nostalgia"),
    (r"\b(map|globe|atlas|geograph)\b", "Maps / geo"),
    (r"\b(learn|vocab|course|tutorial|study|spaced repetition|teach|quiz)\b", "Education / learning"),
    (r"\b(friend|social|collaborat|community|party|stamp|ridiculous|novel)\b", "Social / fun"),
    (r"\b(encrypt|privacy|security|secure|surveillance|honeypot|password)\b", "Security"),
    (r"\b(ai|llm|agent|gpt|neural|machine learning)\b", "AI / ML"),
    (r"\b(font|draw|paint|art|photo|image|poster|color|gradient)\b", "Art / creative"),
    (r"\b(code|git|api|terminal|cli|debug|deploy|regex)\b", "Dev tools"),
]

def rescue(name, tagline, reasoning, local_first):
    if local_first:
        return "Local-first / privacy"
    text = f"{name} {tagline} {reasoning}".lower()
    for pattern, cat in RESCUE:
        if re.search(pattern, text):
            return cat
    return None

def ckey(name, domain):
    """Normalized cache key — matches the dedupe key so casing changes in a
    re-scrape don't silently invalidate cache entries (and re-bill LLM calls)."""
    return f"{(name or '').strip().lower()}|{(domain or '').strip().lower()}"

def main():
    tools = load_tools()
    cache = {}
    if os.path.exists(CACHE):
        for line in open(CACHE):
            line = line.strip()
            if line:
                rec = json.loads(line)
                cache[ckey(rec.get("name"), rec.get("domain"))] = rec

    todo = [t for t in tools
            if ckey(t["name"], t.get("domain")) not in cache]
    print(f"{len(tools)} tools, {len(cache)} cached, {len(todo)} to classify")

    if todo:
        key = load_key()
        with open(CACHE, "a") as cf:
            for bi in range(0, len(todo), BATCH):
                batch = [(bi + i, t["name"], t.get("tagline") or "", t.get("reasoning") or "")
                         for i, t in enumerate(todo[bi:bi + BATCH])]
                for attempt in range(3):
                    try:
                        text = call_api(key, batch)
                        cats = extract_json(text)
                        break
                    except Exception as e:
                        if attempt == 2:
                            print(f"batch {bi} FAILED 3x: {e}")
                            cats = None
                        else:
                            time.sleep(2 * (attempt + 1))
                if cats is None:
                    continue
                for item in batch:
                    idx, name = item[0], item[1]
                    try:
                        c = cats.get(str(idx - bi)) or cats.get(idx - bi) or {}
                        cat = c.get("category", "Other")
                        if cat not in CATEGORIES:
                            cat = "Other"
                        domain = todo[idx].get("domain") or ""
                        rec = {"key": ckey(name, domain), "name": name, "domain": domain,
                               "category": cat,
                               "confidence": float(c.get("confidence", 0)),
                               "local_first": bool(c.get("local_first", False)),
                               "why": str(c.get("why", ""))[:80]}
                    except Exception as e:
                        print(f"  skipped {name!r}: malformed entry ({e})")
                        continue
                    cf.write(json.dumps(rec) + "\n")
                    cache[ckey(rec.get("name"), rec.get("domain"))] = rec
                cf.flush()
                print(f"batch {bi // BATCH + 1}/{(len(todo) + BATCH - 1) // BATCH} done ({len(batch)}/{len(batch)})")
                time.sleep(0.3)

    out = {}
    rescued = 0
    for t in tools:
        k = ckey(t["name"], t.get("domain"))
        if k not in cache:
            continue
        rec = cache[k]
        cat = rec["category"]
        if cat == "Other":
            r = rescue(t["name"], t.get("tagline") or "", t.get("reasoning") or "", rec["local_first"])
            if r:
                cat = r
                rescued += 1
        out[t["name"]] = {"category": cat, "confidence": rec["confidence"],
                          "local_first": rec["local_first"], "why": rec["why"]}
    json.dump(out, open(OUT, "w"), indent=1)
    from collections import Counter
    dist = Counter(v["category"] for v in out.values())
    lf = sum(1 for v in out.values() if v["local_first"])
    print(f"classified: {len(out)}/{len(tools)}  local_first: {lf}  rescued-from-Other: {rescued}")
    for c, n in dist.most_common():
        print(f"  {c:22s} {n}")

if __name__ == "__main__":
    main()
