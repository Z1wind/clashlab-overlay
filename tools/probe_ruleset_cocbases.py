# -*- coding: utf-8 -*-
import glob, json, os, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
files = sorted(glob.glob(os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main", "rulesets", "home-*.json")))
print("rulesets:", [os.path.basename(f) for f in files])
if files:
    d = json.load(open(files[-1], encoding="utf-8"))
    print("latest:", os.path.basename(files[-1]), "type:", type(d).__name__)
    if isinstance(d, dict):
        print("top keys:", list(d.keys())[:12])
        for k in list(d.keys())[:2]:
            v = d[k]
            print("  ", k, "->", json.dumps(v, ensure_ascii=False)[:500] if not isinstance(v, list) else ("list len %d" % len(v)))
            if isinstance(v, list) and v:
                print("   first:", json.dumps(v[0], ensure_ascii=False)[:400])
# cocbases REST
print("---- cocbases REST ----")
for u in ("https://cocbases.com/wp-json/wp/v2/posts?per_page=5",
          "https://cocbases.com/wp-json/wp/v2/types"):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 clashlab"})
        with urllib.request.urlopen(req, timeout=40) as r:
            txt = r.read().decode("utf-8", "ignore")
        print(u, "->", len(txt), txt[:300].replace(chr(10), " "))
    except Exception as e:
        print(u, "ERR", str(e)[:100])
