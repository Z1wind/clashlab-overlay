# -*- coding: utf-8 -*-
"""恢复映射 v2：已知 23 个候选 id + 8 并发下载 + 增量落盘。"""
import concurrent.futures as cf, hashlib, io, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D = os.path.join(BASE, "android", "assets", "img"); UA = {"User-Agent": "Mozilla/5.0"}
def encode(data):
    im = Image.open(io.BytesIO(data)).convert("RGB"); w, h = im.size
    if w > 1600: im = im.resize((1600, int(h * 1600.0 / w)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88, optimize=True); return buf.getvalue()
local = {}
for f in sorted(os.listdir(D)):
    if f.startswith("b") and f.endswith(".jpg"):
        local[hashlib.md5(open(os.path.join(D, f), "rb").read()).hexdigest()] = f
print("local:", len(local), flush=True)
cands = ([("war", n) for n in range(1, 10)] + [("war", n) for n in range(138, 145)]
         + [("defence", 17)] + [("defence", n) for n in range(81, 87)])
def fetch_one(kind, n):
    url = "https://clashofclans-layouts.com/pics/th16_plans/%s/original/th16_%s_%d.jpg" % (kind, kind, n)
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
        h = hashlib.md5(encode(data)).hexdigest()
        return (kind, n, h)
    except Exception as e:
        return (kind, n, None)
mapping = {}
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for kind, n, h in ex.map(lambda a: fetch_one(*a), cands):
        if h in local:
            mapping[local[h]] = {"kind": kind, "id": n}
            print("match", local[h], "<-", kind, n, flush=True)
out = os.path.join(BASE, "out", "layouts_src", "mapping.json")
json.dump(mapping, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("mapped:", len(mapping), "/", len(local), flush=True)
