# -*- coding: utf-8 -*-
import urllib.request, re
def fetch(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) clashlab-research"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", type(e).__name__ + ":" + str(e)[:80]
urls = [
 "https://clashofclans.fandom.com/wiki/Hidden_Tesla",
 "https://clashofclans.fandom.com/wiki/Giant_Arrow",
 "https://coc.guide/equipment/giant-arrow/",
 "https://www.clashofclans.com/blog",
]
for u in urls:
    st, body = fetch(u)
    print("==", u, "->", st, "| len", len(body) if isinstance(body, str) else 0)
    if st == 200:
        txt = re.sub(r"<[^>]+>", " ", body)
        txt = re.sub(r"\s+", " ", txt)
        for kw in ("invisible", "hidden", "DPS", "damage", "Giant Arrow", "tesla"):
            i = txt.lower().find(kw.lower())
            if i > 0:
                print("   ", kw, ":", txt[max(0, i-120):i+240][:340])
                break
