# -*- coding: utf-8 -*-
"""检查候选仓库里是否有 base-link 解码逻辑（打印上下文）。"""
import re, urllib.request

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 clashlab"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "ignore")

files = {
    "baselinkhub/app.js": "https://raw.githubusercontent.com/rudrolab/baselinkhub/main/js/app.js",
    "coctimer/bases.js": "https://raw.githubusercontent.com/sqggde/coctimer/main/js/bases.js",
    "clash-buddy/th16.json": "https://cdn.jsdelivr.net/gh/Wire15/clash-buddy@main/content/layouts/th16.json",
}
for name, u in files.items():
    try:
        txt = get(u)
    except Exception as e:
        print(name, "ERR", str(e)[:80]); continue
    print("=" * 20, name, len(txt))
    for kw in ("base64", "decode", "atob", "?id=", "OpenLayout", "TH16"):
        for m in list(re.finditer(re.escape(kw), txt, re.I))[:2]:
            s = max(0, m.start() - 120); e = min(len(txt), m.end() + 160)
            frag = txt[s:e].replace("\n", " ")
            print("  [%s] ...%s..." % (kw, frag[:260]))
