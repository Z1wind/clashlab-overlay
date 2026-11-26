# -*- coding: utf-8 -*-
import json, os, time, urllib.parse, urllib.request, urllib.error
TOKEN = os.environ["GH_TOKEN"]
def search(q, per=8):
    u = "https://api.github.com/search/repositories?q=%s&per_page=%d&sort=stars" % (urllib.parse.quote(q), per)
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:120]}
for q in ("clash of clans battle simulation", "coc war simulator", "clash of clans wargame",
          "clash of clans attack simulator", "clan war attack planner"):
    r = search(q)
    print("==", q, "->", r.get("total_count", r.get("_err")))
    for it in r.get("items", [])[:5]:
        print("   %-34s %-8s stars=%-5s | %s" % (it["full_name"], it.get("language") or "-",
                                                 it["stargazers_count"], (it.get("description") or "")[:80]))
    time.sleep(1)
