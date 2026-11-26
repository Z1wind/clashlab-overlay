# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def exists(p):
    try:
        u = REPO + "/contents/" + urllib.parse.quote(p)
        h = {"Authorization": "token " + TOKEN, "User-Agent": "c"}
        with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=30) as r:
            return json.loads(r.read().decode()).get("size")
    except Exception as e:
        return "MISSING"
import urllib.parse
for p in ("models/v2_all/recog_v2_all.pt", "models/v2_defense/recog_v2_def.pt",
          "models/all6_defense/recog_all6_def.pt", "models/synth_level.pt",
          "docs/LEVELS.md", "docs/ANDROID_APP.md", "docs/STRATEGY.md", "docs/WARGAME.md"):
    print("%-42s %s" % (p, exists(p)))
m = json.loads(urllib.request.urlopen(urllib.request.Request(REPO, headers={"Authorization": "token " + TOKEN, "User-Agent": "c"}), timeout=30).read())
print("description:", (m.get("description") or "")[:100])
print("topics:", len(m.get("topics") or []))
