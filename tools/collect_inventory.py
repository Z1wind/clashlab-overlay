# -*- coding: utf-8 -*-
import glob, json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "live", "scouts")
keep = {"map_01.png", "map_01.json", "scout_01_6a402f3c30.png", "scout_01_6a402f3c30.json",
        "war_01_LR8GVY892.png", "war_01.json", "war_01_92PPC2RVQ.png"}
removed = 0
for f in glob.glob(os.path.join(OUT, "*")):
    b = os.path.basename(f)
    if b.startswith("_") or (b not in keep and (b.startswith("map_") or b.startswith("scout_") or b.startswith("war_"))):
        try:
            os.remove(f); removed += 1
        except Exception:
            pass
print("removed", removed)
rows = []
for f in sorted(glob.glob(os.path.join(OUT, "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    p = (d.get("api") or {}).get("player") or {}
    rows.append({"file": os.path.basename(f), "name": d.get("ocr", {}).get("name"),
                 "clan": d.get("ocr", {}).get("clan"), "tag": p.get("tag"), "th": p.get("th")})
print(rows)

# 文档更新
BT = chr(96)
p = os.path.join(BASE, "docs", "LIVE_TEST.md")
t = open(p, encoding="utf-8").read()
add = '''
## 战图收集（2026-11-26 21:2x，用户逐个点开敌方基地）

| 文件 | OCR 名字 | 部落 | tag | TH |
|---|---|---|---|---|
@@ROWS@@

- 采集器 @tools/war_map_collect3.py@：按 API tag 去重、8 分钟窗口；
- 修复：玩家名折行（SUVRO / Sumon 2）曾被当成两个字段，现在 >=3 行时最后一行才是部落，中间并入名字；新增测试。
'''.replace("@@ROWS@@", "\n".join("| %s | %s | %s | %s | %s |" % (r["file"], r["name"], r["clan"], r["tag"], r["th"]) for r in rows)).replace("@@", BT)
if "战图收集" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("doc updated")
