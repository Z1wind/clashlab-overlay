# -*- coding: utf-8 -*-
"""恢复 b01..b20 ↔ clashofclans-layouts 来源 id 的映射（按 md5 匹配重编码结果）。"""
import hashlib, io, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D = os.path.join(BASE, "android", "assets", "img")
UA = {"User-Agent": "Mozilla/5.0"}
def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
def encode(data):
    im = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = im.size
    if w > 1600:
        im = im.resize((1600, int(h * 1600.0 / w)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88, optimize=True)
    return buf.getvalue()
# 已有图 md5 -> 文件名
local = {}
for f in sorted(os.listdir(D)):
    if f.startswith("b") and f.endswith(".jpg"):
        local[hashlib.md5(open(os.path.join(D, f), "rb").read()).hexdigest()] = f
print("local images:", len(local))
cands = []
for n in range(1, 30): cands.append(("war", n))
for n in range(1, 20): cands.append(("war", 130 + n))
for n in range(1, 20): cands.append(("defence", n))
for n in range(75, 95): cands.append(("defence", n))
mapping = {}
for kind, n in cands:
    if len(mapping) == len(local):
        break
    url = "https://clashofclans-layouts.com/pics/th16_plans/%s/original/th16_%s_%d.jpg" % (kind, kind, n)
    try:
        data = get(url)
    except Exception:
        continue
    h = hashlib.md5(encode(data)).hexdigest()
    if h in local and h not in mapping:
        mapping[h] = {"file": local[h], "kind": kind, "id": n}
        print("match", local[h], "<-", kind, n)
out = os.path.join(BASE, "out", "layouts_src", "mapping.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(mapping, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("mapped:", len(mapping), "/", len(local))
