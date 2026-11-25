# -*- coding: utf-8 -*-
"""第 3 步：网格扫屏采集标签（tap → 固定名卡区域 OCR → 记录）。

实测：全 base 视野下，点建筑后名称卡片固定在底部中央，文本约在 x 470..820 / y 455..505。
本脚本不按 BACK（会弹“确定退出”），用后续点击自然切换选择。
"""
import json, os, sys, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import al_drive as d
import al_ocr

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label")
CARD = (430, 440, 860, 522)   # 名称卡区域 x0,y0,x1,y1（实测，留余量）
INFO_WORDS = ["信息", "等级", "生命", "伤害", "射程", "数量", "我的等级"]


def read_name(img):
    x0, y0, x1, y1 = CARD
    reg = img[y0:y1, x0:x1]
    pim = al_ocr.preprocess(reg)
    if pim is None:
        return None, None, []
    res = al_ocr.ocr(pim)
    lines = [l.get("text", "") for l in res.get("lines", [])]
    typ, kw = al_ocr.classify(" ".join(lines))
    return typ, kw, lines


def grid_points(x0=150, x1=1140, y0=80, y1=680, step=45):
    pts = []
    for y in range(y0, y1, step):
        for x in range(x0, x1, step):
            pts.append((x, y))
    return pts


def sweep(points, tag, wait=0.85, save_crops=True):
    os.makedirs(os.path.join(OUT, "sweep"), exist_ok=True)
    labels_path = os.path.join(OUT, "%s_labels.json" % tag)
    done = {}
    if os.path.exists(labels_path):
        for r in json.load(open(labels_path, encoding="utf-8")):
            done[(r["x"], r["y"])] = r
    results = list(done.values())
    t0 = time.time()
    for i, (x, y) in enumerate(points):
        if (x, y) in done:
            continue
        d.tap(x, y, "sweep")
        time.sleep(wait)
        img = d.shot()
        typ, kw, lines = read_name(img)
        rec = {"i": i, "x": x, "y": y, "type": typ, "kw": kw,
               "lines": [l for l in lines if len(l) <= 20][:6]}
        if typ and save_crops:
            crop = img[CARD[1]:CARD[3], CARD[0]:CARD[2]]
            cv2.imencode(".png", crop)[1].tofile(os.path.join(OUT, "sweep", "%s_%d_%d.png" % (tag, x, y)))
        results.append(rec)
        if (i + 1) % 20 == 0:
            json.dump(results, open(labels_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            hit = sum(1 for r in results if r["type"])
            print("progress %d/%d hit=%d %.0fs" % (i + 1, len(points), hit, time.time() - t0))
    json.dump(results, open(labels_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    hit = sum(1 for r in results if r["type"])
    print("DONE points=%d hit=%d" % (len(results), hit))
    return results


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "test":
        pts = [(890, 380), (640, 300), (500, 250), (300, 200), (760, 430), (420, 350),
               (950, 300), (700, 200), (560, 480), (860, 200), (250, 300), (1020, 420)]
        sweep(pts, "t1")
    else:
        tag = sys.argv[2] if len(sys.argv) > 2 else "g1"
        step = int(sys.argv[3]) if len(sys.argv) > 3 else 45
        sweep(grid_points(step=step), tag)
