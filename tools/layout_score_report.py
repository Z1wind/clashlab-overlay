# -*- coding: utf-8 -*-
"""对六阵跑 P3b-1 防守评分，输出 json + markdown 报告。"""
import os, sys, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.layout_score import score_layout, load_layout

OUT = os.path.join(BASE, "out", "overlay", "_p3b")
os.makedirs(OUT, exist_ok=True)
base_dir = os.path.join(BASE, "bases", "th16")
rows = []
for name in sorted(os.listdir(base_dir)):
    p = os.path.join(base_dir, name, "layout.json")
    if not os.path.exists(p):
        continue
    r = score_layout(load_layout(p))
    rows.append({"base": name, **r})
    print("%s  score=%5.1f grade=%s  metrics=%s" % (
        name, r["overall"], r["grade"],
        " ".join("%s=%.0f" % (m["id"].split("-")[0], m["score"]) for m in r["metrics"])), flush=True)

json.dump(rows, open(os.path.join(OUT, "layout_scores.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

lines = ["# P3b-1 六阵防守评分（移植 clash-blueprint-engine analyzer）", "",
         "| 阵 | 总分 | 等级 | 大本营 | 仓库 | 对空 | 对地 | 隔间 | 墙体 | 入口 |",
         "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    m = {x["id"]: x["score"] for x in r["metrics"]}
    lines.append("| %s | **%.1f** | %s | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f | %.0f |" % (
        r["base"], r["overall"], r["grade"],
        m.get("town-hall-protection", 0), m.get("storage-protection", 0),
        m.get("air-coverage", 0), m.get("ground-coverage", 0),
        m.get("compartment-quality", 0), m.get("wall-efficiency", 0), m.get("entry-points", 0)))
lines += ["", "## 弱点 Top3（按严重度排序）", ""]
for r in rows:
    lines.append("### %s（%.1f / %s）" % (r["base"], r["overall"], r["grade"]))
    for w in r["weakPoints"][:3]:
        lines.append("- [%s] %s -> %s" % (w["severity"], w["message"], w.get("recommendation", "")))
    lines.append("")
open(os.path.join(OUT, "layout_scores.md"), "w", encoding="utf-8").write("\n".join(lines))
print("saved", os.path.join(OUT, "layout_scores.json"), os.path.join(OUT, "layout_scores.md"))
