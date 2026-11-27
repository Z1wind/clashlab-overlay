# -*- coding: utf-8 -*-
"""汇总 6 套阵的报告 + 画俯视箭线示意图。"""
import glob, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
AIR = {"air-defense", "air-sweeper"}
rows = []
for d in sorted(glob.glob(os.path.join(BASE, "out", "enemy_report", "0*"))):
    r = json.load(open(os.path.join(d, "report.json"), encoding="utf-8"))
    sc = r.get("score") or {}
    b = r.get("arrow_best") or {}
    hits = b.get("hits") or []
    air_hits = [h for h in hits if isinstance(h, dict) and h.get("type") in AIR] if hits else []
    row = {"base": os.path.basename(d), "name": (sc.get("name") or r.get("name") or "")[:28],
           "overall": sc.get("overall"), "grade": sc.get("grade"),
           "buildings": r.get("buildings"),
           "arrow_from": b.get("from"), "arrow_to": b.get("to"),
           "hits": len(hits), "air_hits": len(air_hits), "warning": (b.get("tesla_warning") or "")[:30],
           "candidates": len(r.get("arrow_candidates") or [])}
    rows.append((d, row, r))
    print("%-14s %-28s score=%5s %s bldg=%3s arrow %s->%s hits=%s air=%s cands=%s" % (
        row["base"], row["name"], row["overall"], row["grade"], row["buildings"],
        row["arrow_from"], row["arrow_to"], row["hits"], row["air_hits"], row["candidates"]))

# 俯视示意图
for d, row, r in rows:
    lay = json.load(open(os.path.join(BASE, r["layout"]), encoding="utf-8")) if r.get("layout") else {}
    blds = lay.get("buildings") or []
    S = 640; M = 30; N = 44
    img = np.full((S, S, 3), 34, np.uint8)
    def P(x, y):
        return (int(M + x / N * (S - 2 * M)), int(M + y / N * (S - 2 * M)))
    for g in range(0, N + 1, 4):
        cv2.line(img, P(g, 0), P(g, N), (60, 60, 60), 1)
        cv2.line(img, P(0, g), P(N, g), (60, 60, 60), 1)
    for b in blds:
        t = b.get("type"); x, y = b.get("tile") or [0, 0]
        col = (60, 200, 60) if t == "air-sweeper" else ((60, 60, 230) if t == "air-defense" else (150, 150, 150))
        cv2.circle(img, P(x + 1.5, y + 1.5), 4, col, -1)
    b = r.get("arrow_best") or {}
    if b.get("from") and b.get("to"):
        p0 = P(b["from"][0], b["from"][1]); p1 = P(b["to"][0], b["to"][1])
        cv2.arrowedLine(img, p0, p1, (0, 210, 255), 3, tipLength=0.06)
    cv2.putText(img, "%s  %s (%s)" % (row["base"], row["overall"], row["grade"]), (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1)
    cv2.imencode(".png", img)[1].tofile(os.path.join(d, "arrow_diagram.png"))
print("diagrams saved")
