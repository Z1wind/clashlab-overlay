# -*- coding: utf-8 -*-
"""从 clashofclans-layouts.com 抓取不同阵型原图，作为「标 4 角」数据源（含不同背景/皮肤）。"""
import json, os, re, urllib.request

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "sceneries")
os.makedirs(OUT, exist_ok=True)
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) clashlab-research"}

def fetch(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def get_html(url):
    return fetch(url).decode("utf-8", "ignore")

targets = []
for th in (12, 13, 14, 15, 16, 17):
    for kind in ("war", "defence"):
        url = "https://clashofclans-layouts.com/plans/th_%d/" % th
        try:
            html = get_html(url)
        except Exception as e:
            print("list fail", th, kind, str(e)[:60]); continue
        pat = r"/pics/th%s_plans/%s/original/([a-z0-9_]+)\.jpg" % (th, kind if kind == "war" else "defence")
        found = re.findall(pat, html)
        targets += [(th, kind, n) for n in found[:4]]
print("candidates:", len(targets))
meta = []
for th, kind, name in targets:
    k = "war" if kind == "war" else "defence"
    src = "https://clashofclans-layouts.com/pics/th%d_plans/%s/original/%s.jpg" % (th, k, name)
    dst = os.path.join(OUT, "th%d_%s_%s.jpg" % (th, k, name))
    if os.path.exists(dst) and os.path.getsize(dst) > 20000:
        continue
    try:
        data = fetch(src)
        open(dst, "wb").write(data)
        meta.append({"file": os.path.basename(dst), "th": th, "kind": k, "name": name,
                     "source": src, "bytes": len(data)})
        print("saved", os.path.basename(dst), len(data))
    except Exception as e:
        print("img fail", name, str(e)[:60])
json.dump(meta, open(os.path.join(OUT, "_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", len(meta))
