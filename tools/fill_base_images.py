# -*- coding: utf-8 -*-
"""补齐到 20 张：去重 + HEAD 探测更多 TH16 原图。"""
import hashlib, io, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG_DIR = os.path.join(BASE, "android", "assets", "img")
UA = {"User-Agent": "Mozilla/5.0"}

def get(url, timeout=90):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()

def try_url(kind, n):
    url = "https://clashofclans-layouts.com/pics/th16_plans/%s/original/th16_%s_%d.jpg" % (kind, kind, n)
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status == 200 and int(r.headers.get("Content-Length") or 0) > 50000:
                return url
    except Exception:
        return None
    return None

# 1) 去重现有
files = sorted(f for f in os.listdir(IMG_DIR) if f.startswith("b") and f.endswith(".jpg"))
seen = {}
keep = []
for f in files:
    p = os.path.join(IMG_DIR, f)
    h = hashlib.md5(open(p, "rb").read()).hexdigest()
    if h in seen:
        print("dup removed", f, "==", seen[h])
        os.remove(p)
    else:
        seen[h] = f
        keep.append(p)
print("unique existing:", len(keep))

# 2) 探测更多
need = 20 - len(keep)
found = []
for kind, rng in (("war", range(1, 161)), ("defence", range(1, 121))):
    if need <= 0:
        break
    for n in rng:
        if need <= 0:
            break
        url = try_url(kind, n)
        if not url:
            continue
        try:
            data = get(url)
        except Exception:
            continue
        h = hashlib.md5(data).hexdigest()
        if h in seen:
            continue
        im = Image.open(io.BytesIO(data)).convert("RGB")
        w, hgt = im.size
        if w > 1600:
            im = im.resize((1600, int(hgt * 1600.0 / w)), Image.LANCZOS)
        dst = os.path.join(IMG_DIR, "b%02d.jpg" % (len(keep) + len(found) + 1))
        im.save(dst, "JPEG", quality=88, optimize=True)
        seen[h] = dst
        found.append(dst)
        need -= 1
        print("added", os.path.basename(dst), kind, n, im.size, os.path.getsize(dst), "bytes")
print("total now:", len(keep) + len(found))
