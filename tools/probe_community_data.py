# -*- coding: utf-8 -*-
"""探查 cocbases.com 列表页与图片 URL；jsdelivr 数据仓库结构。"""
import json, re, urllib.request

def fetch(u, timeout=40):
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) clashlab"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

for u in ("https://cocbases.com/th16/war", "https://cocbases.com/th16/war/"):
    try:
        h = fetch(u).decode("utf-8", "ignore")
        print("==", u, "len", len(h))
        imgs = sorted(set(re.findall(r'https://cocbases\.com/wp-content/uploads/[^"\' ]+\.(?:webp|jpg|png|jpeg)', h)))
        print("imgs:", len(imgs), imgs[:6])
        links = sorted(set(re.findall(r'https://cocbases\.com/[a-z0-9\-]+/[a-z0-9\-]+/?[^"\' ]*', h)))[:8]
        print("links sample:", links[:5])
    except Exception as e:
        print("==", u, "ERR", str(e)[:80])

print("---- jsdelivr data repos ----")
for repo in ("chiefpansancolt/clash-of-clans-data", "Statscell/clash-of-clans-data"):
    try:
        d = json.loads(fetch("https://data.jsdelivr.com/v1/packages/gh/%s@main?structure=flat" % repo))
        files = [f["name"] for f in d.get("files", [])]
        print(repo, "files:", len(files))
        for f in files[:20]:
            print("  ", f)
    except Exception as e:
        print(repo, "ERR", str(e)[:80])
