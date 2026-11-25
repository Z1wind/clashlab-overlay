# -*- coding: utf-8 -*-
import json, os, time, urllib.parse, urllib.request, urllib.error
TOKEN = os.environ["GH_TOKEN"]
def search(kind, q, per=10):
    url = "https://api.github.com/search/%s?q=%s&per_page=%d" % (kind, urllib.parse.quote(q), per)
    req = urllib.request.Request(url, headers={"Authorization": "token " + TOKEN, "User-Agent": "c",
                                               "Accept": "application/vnd.github.text-match+json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:160]}
for kind, q in [
    ("code", '"buildings" "tile" clash layout'),
    ("code", '"tile": ['),
    ("code", 'clash "layout.json" "town-hall"'),
    ("code", '"grid": 44'),
    ("repositories", 'clash of clans layout json data'),
    ("repositories", 'coc layout editor json'),
]:
    r = search(kind, q)
    if "_err" in r:
        print(kind, q, "->", r["_err"], r["_body"][:80]); time.sleep(2); continue
    print(kind, "|", q, "->", r.get("total_count"))
    for it in r.get("items", [])[:5]:
        print("   ", it.get("full_name") or it.get("path"), "|", (it.get("html_url") or "")[:100])
    time.sleep(2)
