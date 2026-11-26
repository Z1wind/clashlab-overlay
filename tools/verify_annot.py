# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.request, urllib.parse, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for c in get(REPO + "/commits?per_page=1"):
    print("remote:", c["sha"][:8], c["commit"]["message"].splitlines()[0][:80])
for p in ("tools/annotate_web.py", "tools/enemy_pipeline.py", "docs/ANNOTATE_WEB.md", "tests/test_annotate_web.py", "README.md"):
    local = open(os.path.join(BASE, p), "rb").read()
    rb = base64.b64decode(get(REPO + "/contents/" + urllib.parse.quote(p))["content"].replace("\n", ""))
    print("%-34s %6d B match=%s" % (p, len(local), hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()))
rep = json.load(open(os.path.join(BASE, "out", "enemy_report", "report.json"), encoding="utf-8"))
print("smoke report:", {"name": rep.get("name"), "buildings": rep.get("buildings"),
      "overall": (rep.get("score") or {}).get("overall"), "grade": (rep.get("score") or {}).get("grade"),
      "arrow_score": (rep.get("arrow_best") or {}).get("score"),
      "placement": rep.get("placement")})
