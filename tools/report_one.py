# -*- coding: utf-8 -*-
"""一条命令出敌方阵报告：pipeline → report.json + arrow_diagram.png + summary.md。"""
import argparse, json, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIR = {"air-defense", "air-sweeper"}

def render(lay, rep, png_path):
    blds = lay.get("buildings") or []
    S, M, N = 640, 30, 44
    img = np.full((S, S, 3), 34, np.uint8)
    def P(x, y):
        return (int(M + x / N * (S - 2 * M)), int(M + y / N * (S - 2 * M)))
    for g in range(0, N + 1, 4):
        cv2.line(img, P(g, 0), P(g, N), (60, 60, 60), 1)
        cv2.line(img, P(0, g), P(N, g), (60, 60, 60), 1)
    for b in blds:
        t = b.get("type"); x, y = (b.get("tile") or [0, 0])[:2]
        col = (60, 200, 60) if t == "air-sweeper" else ((60, 60, 230) if t == "air-defense" else (150, 150, 150))
        cv2.circle(img, P(x + 1.5, y + 1.5), 4, col, -1)
    b = rep.get("arrow_best") or {}
    if b.get("from") and b.get("to"):
        cv2.arrowedLine(img, P(*b["from"]), P(*b["to"]), (0, 210, 255), 3, tipLength=0.06)
    sc = rep.get("score") or {}
    cv2.putText(img, "%s  %s (%s)" % (os.path.basename(png_path), sc.get("overall"), sc.get("grade")),
                (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1)
    cv2.imencode(".png", img)[1].tofile(png_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--queen", default=None)
    a = ap.parse_args()
    lay = json.load(open(a.layout, encoding="utf-8"))
    name = os.path.splitext(os.path.basename(a.layout))[0]
    out = a.out or os.path.join(BASE, "out", "enemy_report", name + "_one")
    os.makedirs(out, exist_ok=True)
    cmd = [sys.executable, os.path.join(BASE, "tools", "enemy_pipeline.py"), "--layout", a.layout, "--out", out]
    if a.queen:
        cmd += ["--queen", a.queen]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("pipeline failed:", r.stderr[-400:])
        return r.returncode
    rep = json.load(open(os.path.join(out, "report.json"), encoding="utf-8"))
    render(lay, rep, os.path.join(out, "arrow_diagram.png"))
    sc = rep.get("score") or {}
    b = rep.get("arrow_best") or {}
    hits = b.get("hits") or []
    air = len([h for h in hits if isinstance(h, dict) and h.get("type") in AIR])
    wps = (sc.get("weakPoints") or [])[:3]
    md = ["# %s" % name, "",
          "- 建筑数：%s" % rep.get("buildings"),
          "- 评分：**%s**（%s）" % (sc.get("overall"), sc.get("grade")),
          "- 穿云箭最优：%s → %s，命中 %s（对空 %s）" % (b.get("from"), b.get("to"), len(hits), air),
          "- 候选线：%s 条" % len(rep.get("arrow_candidates") or []), ""]
    if wps:
        md += ["## 主要弱点"] + ["- [%s] %s → %s" % (w.get("severity"), w.get("message"), w.get("recommendation")) for w in wps] + [""]
    open(os.path.join(out, "summary.md"), "w", encoding="utf-8").write("\n".join(md))
    print("OK", out, "score", sc.get("overall"), sc.get("grade"), "hits", len(hits))

if __name__ == "__main__":
    raise SystemExit(main())
