# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for repo in ("NathanNT/clash-battle-engine", "AbhijnanVegi/coc-attacc", "Himakiyay/clash-attack-ai"):
    try:
        r = get("https://api.github.com/repos/" + repo)
        print("==", repo, "| license:", (r.get("license") or {}).get("spdx_id"), "| stars:", r.get("stargazers_count"),
              "| updated:", r.get("updated_at"), "| desc:", (r.get("description") or "")[:100])
        tree = get("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (repo, r["default_branch"]))
        files = [t["path"] for t in tree.get("tree", []) if t["type"] == "blob"]
        print("   files:", len(files), "|", files[:12])
    except Exception as e:
        print(repo, "ERR", str(e)[:100])
