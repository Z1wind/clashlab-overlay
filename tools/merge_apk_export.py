# -*- coding: utf-8 -*-
"""合并 APK 导出的标注到 out/annotate（保留旧元数据，备份原文件）。"""
import json, os, shutil, time
SRC = r"C:\Users\Admin（无密码）\Downloads\clash_annotate_2026-11-26071640.json"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
A = os.path.join(BASE, "out", "annotate")
ts = time.strftime("%Y%m%d_%H%M%S")
exp = json.load(open(SRC, encoding="utf-8"))
report = {"source": SRC, "merged_at": ts, "bases": []}

def key(x): return (str(x.get("type")), int(x["tile"][0]), int(x["tile"][1]))

for b in exp.get("bases") or []:
    bid = b.get("id")
    p = os.path.join(A, bid + "_annotated.json")
    if not os.path.exists(p):
        print("skip missing", bid); continue
    doc = json.load(open(p, encoding="utf-8"))
    old = doc.get("buildings") or []
    oldmap = {key(x): x for x in old}
    merged = []
    kept = added = 0
    for nb in b.get("buildings") or []:
        k = key(nb)
        item = {"type": str(nb.get("type")), "tile": [int(nb["tile"][0]), int(nb["tile"][1])]}
        if k in oldmap:
            o = oldmap[k]
            for f in ("source", "conf", "note", "level"):
                if f in o:
                    item[f] = o[f]
            if nb.get("level") and not item.get("level"):
                item["level"] = int(nb["level"])
            kept += 1
        else:
            item["source"] = "apk-export"
            item["conf"] = 1.0
            if nb.get("level"):
                item["level"] = int(nb["level"])
            added += 1
        merged.append(item)
    old_n = len(old)
    doc["buildings"] = merged
    doc["name"] = doc.get("name") or b.get("name")
    shutil.copyfile(p, p + ".bak_" + ts)
    json.dump(doc, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    report["bases"].append({"id": bid, "old": old_n, "new": len(merged), "kept": kept, "added": added})
    print("%s: %d -> %d (kept %d, added %d)" % (bid, old_n, len(merged), kept, added))

json.dump(report, open(os.path.join(A, "merge_apk_export_%s.json" % ts), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("report written, ts=", ts)
