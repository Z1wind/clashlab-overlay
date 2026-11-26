# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
allrepos = []
for page in (1, 2):
    allrepos += get("https://api.github.com/users/drkostas/repos?per_page=100&page=%d" % page)
print("total repos:", len(allrepos))
kw = ("clash", "coc", "wargame", "war-game", "simulat", "tactic", "battle", "strategy", "board", "chess", "battleship")
for r in allrepos:
    blob = (r["name"] + " " + (r.get("description") or "") + " " + " ".join(r.get("topics") or [])).lower()
    if any(k in blob for k in kw):
        print("  %-36s stars=%-4s %s | %s" % (r["name"], r.get("stargazers_count"), r.get("language"), (r.get("description") or "")[:100]))
# forks maybe
print("--- forks ---")
for r in allrepos:
    if r.get("fork"):
        print("  fork:", r["name"], "from", r.get("full_name"), "|", (r.get("description") or "")[:60])
