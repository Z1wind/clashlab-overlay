# -*- coding: utf-8 -*-
"""探查 cocbases.com 是否暴露 layout 坐标/链接数据。"""
import re, urllib.request

def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) clashlab"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.read().decode("utf-8", "ignore")

for u in ("https://cocbases.com/", "https://cocbases.com/th16/war"):
    try:
        st, txt = get(u)
        print("==", u, st, "len", len(txt))
        for kw in ("OpenLayout", "link.clashofclans", "tile", "coordinate", "json", "data-", "canvas", "svg", "layout"):
            hits = [m.start() for m in re.finditer(re.escape(kw), txt, re.I)][:2]
            if hits:
                print("   [%s] x%d | %s" % (kw, len(hits), txt[max(0,hits[0]-60):hits[0]+120].replace("\n"," ")[:200]))
    except Exception as e:
        print("==", u, "ERR", str(e)[:90])
