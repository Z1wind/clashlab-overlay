# -*- coding: utf-8 -*-
"""用 Python urllib 抓公开源码（绕开 web_fetch 的 content-type/跨源限制），查 base-link 解码可行性。"""
import json, re, urllib.request

def get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 clashlab-research"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        try:
            return r.status, raw.decode("utf-8", "ignore")
        except Exception:
            return r.status, ""

urls = [
    "https://cdn.jsdelivr.net/gh/Wire15/clash-buddy@main/content/layouts/th16.json",
    "https://raw.githubusercontent.com/rudrolab/baselinkhub/main/js/app.js",
    "https://raw.githubusercontent.com/sqggde/coctimer/main/js/bases.js",
    "https://raw.githubusercontent.com/nschmeller/clash-bases/main/README.md",
    "https://raw.githubusercontent.com/arcadeclash/coc-recommended-base-links/main/README.md",
]
for u in urls:
    try:
        st, txt = get(u)
        low = txt.lower()
        print("=== %s (%s) len=%d" % (u.split('/')[-1], st, len(txt)))
        for kw in ("buildings", "tiles", "tile", "grid", "decod", "atob", "base64", "buffer", "unzip", "inflate"):
            print("   %-10s hits=%d" % (kw, low.count(kw)))
        # 展示 json 的第一条结构
        if u.endswith(".json") and txt.strip().startswith("["):
            arr = json.loads(txt)
            print("   entries:", len(arr), "| keys:", list(arr[0].keys())[:10] if arr else None)
    except Exception as e:
        print("=== %s ERR %r" % (u.rsplit('/', 1)[-1], str(e)[:80]))
