# -*- coding: utf-8 -*-
# asset_draw.py — 把命中框画到块联系表 / 侦察帧上（18类分色）
import os, json, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLKDIR = os.path.join(ROOT, "out", "overlay", "blocks")

COLORS = {
 "airdef": (0,0,255), "archertower": (0,165,255), "bombtower": (0,255,255),
 "cannon": (0,255,0), "collector": (255,128,0), "eagle": (128,0,255),
 "firespitter": (255,0,255), "inferno": (0,128,255), "monolith": (128,128,0),
 "mortar": (255,0,128), "multiarcher": (64,220,220), "scatter": (128,255,0),
 "spelltower": (200,0,0), "storage": (255,215,0), "sweeper": (0,200,200),
 "tesla": (180,100,255), "townhall": (255,80,80), "wiztower": (80,80,255),
 "xbow": (0,90,0), "wall": (120,120,120),
}

def draw_l2():
    d = json.load(open(os.path.join(ROOT, "out", "recog", "asset_raw_l2.json"), encoding="utf-8"))
    # 每块画框
    canv = {}
    for ttype, r in d["results"].items():
        col = COLORS.get(ttype, (255,255,255))
        for h in r["hits"]:
            b = h["block"]
            if b not in canv:
                canv[b] = cv2.imdecode(np.fromfile(os.path.join(BLKDIR, b), dtype=np.uint8), cv2.IMREAD_COLOR).copy()
            cv2.rectangle(canv[b], (h["x0"], h["y0"]), (h["x1"], h["y1"]), col, 2)
    # 联系表
    thumbs = []
    for i in range(15):
        b = f"b{i:02d}.png"
        im = canv.get(b, cv2.imdecode(np.fromfile(os.path.join(BLKDIR, b), dtype=np.uint8), cv2.IMREAD_COLOR))
        im = cv2.resize(im, (316, 183))
        cv2.putText(im, b, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        thumbs.append(im)
    rows = [np.hstack(thumbs[r*3:(r+1)*3]) for r in range(5)]
    sheet = np.vstack(rows)
    # 图例
    leg = np.full((120, sheet.shape[1], 3), 255, np.uint8)
    x = 10
    for ttype, col in COLORS.items():
        cv2.rectangle(leg, (x, 10), (x+20, 30), col, -1)
        cv2.putText(leg, ttype, (x+24, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1)
        x += 150
        if x > sheet.shape[1]-160:
            x = 10; leg = np.vstack([leg, np.full((60, sheet.shape[1], 3), 255, np.uint8)])
    out = np.vstack([sheet, leg])
    ok, buf = cv2.imencode(".png", out)
    buf.tofile(os.path.join(ROOT, "out", "overlay", "recog_asset_l2.png"))
    print("saved recog_asset_l2.png", out.shape)

def draw_b14():
    d = json.load(open(os.path.join(ROOT, "out", "recog", "asset_raw_b14.json"), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "enemy", "b14_full.png"), dtype=np.uint8), cv2.IMREAD_COLOR).copy()
    for ttype, r in d["results"].items():
        col = COLORS.get(ttype, (255,255,255))
        for h in r["hits"]:
            cv2.rectangle(img, (h["x0"], h["y0"]), (h["x1"], h["y1"]), col, 2)
    ok, buf = cv2.imencode(".png", img)
    buf.tofile(os.path.join(ROOT, "out", "overlay", "recog_asset_b14.png"))
    print("saved recog_asset_b14.png", img.shape)

draw_l2()
draw_b14()
