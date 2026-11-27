# -*- coding: utf-8 -*-
"""再补 3 张唯一阵图（探测 war/defence 更多 id）。"""
import hashlib, io, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D = os.path.join(BASE, "android", "assets", "img")
UA = {"User-Agent": "Mozilla/5.0"}
def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()
seen = set()
for f in os.listdir(D):
    if f.lower().endswith(".jpg"):
        seen.add(hashlib.md5(open(os.path.join(D, f), "rb").read()).hexdigest())
print("have", len(seen))
count = len([f for f in os.listdir(D) if f.lower().endswith(".jpg")])
found = 0
for kind, rng in (("war", range(7, 120)), ("defence", range(1, 120))):
    if count >= 20:
        break
    for n in rng:
        if count >= 20:
            break
        url = "https://clashofclans-layouts.com/pics/th16_plans/%s/original/th16_%s_%d.jpg" % (kind, kind, n)
        try:
            data = get(url)
        except Exception:
            continue
        h = hashlib.md5(data).hexdigest()
        if h in seen:
            continue
        im = Image.open(io.BytesIO(data)).convert("RGB")
        w, hh = im.size
        if w > 1600:
            im = im.resize((1600, int(hh * 1600.0 / w)), Image.LANCZOS)
        dst = os.path.join(D, "b%02d.jpg" % (count + 1))
        im.save(dst, "JPEG", quality=88, optimize=True)
        seen.add(h); count += 1; found += 1
        print("added", os.path.basename(dst), kind, n, os.path.getsize(dst),"bytes")
print("now:", count, "found:", found)
