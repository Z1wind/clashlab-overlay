# -*- coding: utf-8 -*-
"""下载社区阵型原图（clashofclans-layouts.com），供四角自动标注/训练用。"""
import json, os, re, urllib.request

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "quad_images")
os.makedirs(OUT, exist_ok=True)
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) clashlab-research"}

def fetch(u, timeout=60):
    req = urllib.request.Request(u, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

meta = []
for th in range(9, 19):
    try:
        html = fetch("https://clashofclans-layouts.com/plans/th_%d/" % th).decode("utf-8", "ignore")
    except Exception as e:
        print("th%d list fail %s" % (th, str(e)[:50])); continue
    links = sorted(set(re.findall(r'/plans/th_%d/((?:war|defence)_\d+)\.html' % th, html)))
    picked = links[:5]
    for d in picked:
        try:
            page = fetch("https://clashofclans-layouts.com/plans/th_%d/%s.html" % (th, d)).decode("utf-8", "ignore")
        except Exception:
            continue
        m = re.search(r'href="(/pics/th%d_plans/[a-z]+/original/[^"]+\.(?:jpg|png))"' % th, page)
        if not m:
            continue
        src = "https://clashofclans-layouts.com" + m.group(1)
        fn = "th%d_%s%s" % (th, d, os.path.splitext(src)[1])
        dst = os.path.join(OUT, fn)
        if os.path.exists(dst) and os.path.getsize(dst) > 30000:
            meta.append({"file": fn, "th": th, "source": src, "bytes": os.path.getsize(dst)})
            continue
        try:
            data = fetch(src)
            if len(data) < 20000:
                continue
            open(dst, "wb").write(data)
            meta.append({"file": fn, "th": th, "source": src, "bytes": len(data)})
            print("saved", fn, len(data))
        except Exception as e:
            print("img fail", fn, str(e)[:40])
json.dump(meta, open(os.path.join(OUT, "_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total:", len(meta))
