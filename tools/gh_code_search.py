# -*- coding: utf-8 -*-
"""GitHub 代码搜索：找 OpenLayout / base link 解码器的公开实现。"""
import json, os, urllib.parse, urllib.request, urllib.error, time
TOKEN = os.environ["GH_TOKEN"]
def search(kind, q, per=10):
    url = "https://api.github.com/search/%s?q=%s&per_page=%d" % (kind, urllib.parse.quote(q), per)
    req = urllib.request.Request(url, headers={"Authorization": "token " + TOKEN, "User-Agent": "c",
                                               "Accept": "application/vnd.github.text-match+json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:200]}
queries = [
    ('code', '"action=OpenLayout"'),
    ('code', '"TH16%3AWB"'),
    ('code', 'OpenLayout id=TH'),
    ('repositories', 'clash of clans layout decoder'),
    ('repositories', 'coc base layout parser'),
    ('repositories', 'clash of clans base link'),
]
for kind, q in queries:
    r = search(kind, q)
    if "_err" in r:
        print(kind, q, "->", r["_err"], r["_body"][:100])
    else:
        print(kind, q, "-> total", r.get("total_count"))
        for it in r.get("items", [])[:6]:
            print("   ", it.get("full_name") or it.get("path"), "|", (it.get("html_url") or "")[:90])
    time.sleep(2)
