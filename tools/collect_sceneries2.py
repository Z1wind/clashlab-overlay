# -*- coding: utf-8 -*-
"""抓取不同阵型原图（先列表页取详情链接，再详情页取 original.jpg）。"""
import json, os, re, urllib.request

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "sceneries")
os.makedirs(OUT, exist_ok=True)
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) clashlab-research"}

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def get_html(url):
    return fetch(url).decode("utf-8", "ignore")

rows = []
for th in (10, 12, 13, 14, 15, 16, 17, 18):
    try:
        html = get_html("https://clashofclans-layouts.com/plans/th_%d/" % th)
    except Exception as e:
        print("list fail", th, str(e)[:60]); continue
    links = sorted(set(re.findall(r'/plans/th_%d/((?:war|defence)_\d+)\.html' % th, html)))
    picked = links[:3]
    print("th%d detail links=%d picked=%s" % (th, len(links), picked))
    for d in picked:
        try:
            page = get_html("https://clashofclans-layouts.com/plans/th_%d/%s.html" % (th, d))
        except Exception as e:
            print("  detail fail", d, str(e)[:50]); continue
        m = re.search(r'href="(/pics/th%d_plans/[a-z]+/original/[^"]+\.(?:jpg|png))"' % th, page)
        if not m:
            print("  no original", d); continue
        src = "https://clashofclans-layouts.com" + m.group(1)
        dst = os.path.join(OUT, "th%d_%s%s" % (th, d, os.path.splitext(src)[1]))
        try:
            data = fetch(src, timeout=60)
            open(dst, "wb").write(data)
            rows.append({"file": os.path.basename(dst), "th": th, "detail": d, "source": src, "bytes": len(data)})
            print("  saved", os.path.basename(dst), len(data))
        except Exception as e:
            print("  img fail", d, str(e)[:50])
json.dump(rows, open(os.path.join(OUT, "_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total:", len(rows))
