# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ.get("GH_TOKEN", "")
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def get(url):
    h = {"User-Agent": "c", "Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = "token " + TOKEN
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except Exception as e:
        return {"_err": repr(e)[:120]}

branches = get(REPO + "/branches")
print("branches:", [(b["name"], b["commit"]["sha"][:8]) for b in branches] if isinstance(branches, list) else branches)
cs = get(REPO + "/commits?per_page=20")
print("commits total(page):", len(cs) if isinstance(cs, list) else cs)
for c in (cs if isinstance(cs, list) else [])[:10]:
    print(" ", c["sha"][:8], c["commit"]["message"].splitlines()[0][:60], "| by", (c.get("commit", {}).get("author") or {}).get("name"))
# 检查 .github 目录
gh = get(REPO + "/contents/.github")
print(".github dir:", (gh if isinstance(gh, dict) else [(x["name"], x["type"]) for x in gh]))
# 检查是否有 PR / 其他 ref
refs = get(REPO + "/git/refs")
print("refs:", [(r["ref"]) for r in refs] if isinstance(refs, list) else refs)
