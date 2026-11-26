# -*- coding: utf-8 -*-
import glob, json, os, time
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
A = os.path.join(BASE, "out", "annotate")
files = sorted(glob.glob(os.path.join(A, "*_annotated.json")))
print("annotated files:", len(files))
total_b = 0
changed_type = changed_tile = changed_level = 0
per_level = {}
for p in files:
    doc = json.load(open(p, encoding="utf-8"))
    n = len(doc.get("buildings") or [])
    total_b += n
    bak = p + ".bak_lv"
    old = {}
    if os.path.exists(bak):
        d0 = json.load(open(bak, encoding="utf-8"))
        for b in d0.get("buildings") or []:
            old[(b.get("type"), tuple(b.get("tile") or []))] = b.get("level")
    for b in doc.get("buildings") or []:
        lv = b.get("level")
        per_level[lv] = per_level.get(lv, 0) + 1
        k = (b.get("type"), tuple(b.get("tile") or []))
        if k in old and old[k] != lv:
            changed_level += 1
    m = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(p)))
    print("%s %d 栋 mtime=%s" % (os.path.basename(p), n, m))
print("total buildings:", total_b)
print("levels 分布(前 10):", sorted(per_level.items(), key=lambda x: -x[1])[:10])
print("与满级备份相比 level 变化:", changed_level)
