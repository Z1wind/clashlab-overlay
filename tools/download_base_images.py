# -*- coding: utf-8 -*-
"""下载 15 张新的 TH16 满防阵型原图 + 5 张已有 → 统一 1600 宽 JPEG，存 android/assets/img/b01..b20.jpg。"""
import os, re, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
import io
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG_DIR = os.path.join(BASE, "android", "assets", "img")
os.makedirs(IMG_DIR, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}

def get(url, timeout=90):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()

# 1) 采集可用链接
html = get("https://clashofclans-layouts.com/plans/th_16/").decode("utf-8", "ignore")
links = sorted(set(re.findall(r"/plans/th_16/(war|defence)_(\d+)\.html", html)))
print("links:", len(links))
cands = []
for kind, num in links:
    n = int(num)
    if n <= 0:
        continue
    cands.append((kind, n))
# 去重后取前 15 个（先 war 后 defence）
cands.sort(key=lambda x: (0 if x[0] == "war" else 1, -x[1]))
picked = cands[:15]
print("picked:", picked)
existing = [("war", 138), ("war", 143), ("war", 141), ("war", 139), ("defence", 17)]
allp = existing + picked
out = []
for i, (kind, n) in enumerate(allp, 1):
    url = "https://clashofclans-layouts.com/pics/th16_plans/%s/original/th16_%s_%d.jpg" % (kind, kind, n)
    try:
        data = get(url)
    except Exception as e:
        print("fail", kind, n, str(e)[:80]); continue
    im = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = im.size
    if w > 1600:
        im = im.resize((1600, int(h * 1600.0 / w)), Image.LANCZOS)
    dst = os.path.join(IMG_DIR, "b%02d.jpg" % len(out + [0]) if False else "b%02d.jpg" % (len(out) + 1))
    im.save(dst, "JPEG", quality=88, optimize=True)
    out.append(dst)
    print("saved", os.path.basename(dst), im.size, os.path.getsize(dst), "bytes")
print("total:", len(out))
