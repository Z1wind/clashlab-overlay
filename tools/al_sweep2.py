# -*- coding: utf-8 -*-
"""第 3 步 v2：tap → 信息面板 → OCR 正文（正文是标准字体，识别率高）→ X 关闭。

实测：信息面板标题是描边艺术字（OCR 差），但正文段落是标准黑体，OCR 逐字正确
（例：部队驻扎在兵营。建造并升级兵营以容纳更多部队。）。所以标签从正文里取。
"""
import json, os, sys, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import al_drive as d
import al_ocr

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label")
BODY = (620, 280, 1190, 380)
INFO_BTN = (516, 570)
CLOSE_X = (1131, 48)

NAMES = ["多重箭塔", "弹射加农炮", "隐形特斯拉", "特斯拉电磁塔", "防空火箭", "法师塔", "炸弹塔",
         "地狱之塔", "鹰火炮", "投石炮", "空气炮", "巨石碑", "法术塔", "部落城堡",
         "大本营", "加农炮", "箭塔", "迫击炮", "X连弩", "喷火器", "城墙", "兵营",
         "建筑工人小屋", "金矿", "圣水收集器", "储金罐", "圣水瓶", "黑油钻井", "暗黑重油罐",
         "实验室", "部落小屋", "铁匠铺", "宠物屋", "攻城机器工作坊", "法术工厂", "训练营"]
MAP = {
    "多重箭塔": "multi-archer-tower", "弹射加农炮": "ricochet-cannon", "隐形特斯拉": "hidden-tesla",
    "特斯拉电磁塔": "hidden-tesla", "防空火箭": "air-defense", "法师塔": "wizard-tower",
    "炸弹塔": "bomb-tower", "地狱之塔": "inferno-tower", "鹰火炮": "eagle-artillery",
    "投石炮": "scattershot", "空气炮": "air-sweeper", "巨石碑": "monolith", "法术塔": "spell-tower",
    "部落城堡": "clan-castle", "大本营": "town-hall", "加农炮": "cannon", "箭塔": "archer-tower",
    "迫击炮": "mortar", "X连弩": "x-bow", "喷火器": "firespitter", "城墙": "wall", "兵营": "other",
}


def read_body(img):
    x0, y0, x1, y1 = BODY
    res = al_ocr.ocr(al_ocr.preprocess(img[y0:y1, x0:x1]))
    text = "".join(ch for ch in "".join(l.get("text", "") for l in res.get("lines", [])) if ch.strip())
    return text


def name_from_text(text):
    for n in NAMES:
        if n in text:
            return len(n), n
    return 0, None


def one(x, y):
    d.tap(x, y, "sel")
    time.sleep(0.6)
    d.tap(*INFO_BTN, note="info")
    time.sleep(1.0)
    img = d.shot()
    text = read_body(img)
    d.tap(*CLOSE_X, note="close")
    time.sleep(0.45)
    return text


def grid_points(x0=150, x1=1130, y0=90, y1=545, step=55):
    pts = []
    for y in range(y0, y1, step):
        for x in range(x0, x1, step):
            pts.append((x, y))
    return pts


def sweep(points, tag, save=True):
    os.makedirs(os.path.join(OUT, "sweep2"), exist_ok=True)
    path = os.path.join(OUT, tag + "_labels.json")
    done = {}
    if os.path.exists(path):
        for r in json.load(open(path, encoding="utf-8")):
            done[(r["x"], r["y"])] = r
    results = list(done.values())
    t0 = time.time()
    for i, (x, y) in enumerate(points):
        if (x, y) in done:
            continue
        try:
            text = one(x, y)
        except Exception as e:
            text = ""
        ln, name = name_from_text(text)
        rec = {"x": x, "y": y, "name": name, "type": MAP.get(name, "other" if name else None),
               "text": text[:80]}
        if save and name:
            pass
        results.append(rec)
        if (i + 1) % 10 == 0:
            json.dump(results, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            hit = sum(1 for r in results if r["name"])
            print("progress %d/%d hit=%d %.0fs" % (i + 1, len(points), hit, time.time() - t0))
    json.dump(results, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DONE n=%d hit=%d" % (len(results), sum(1 for r in results if r["name"])))
    return results


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "test":
        pts = [(890, 380), (640, 300), (500, 250), (300, 200), (760, 430), (700, 200), (950, 300), (560, 480)]
        sweep(pts, "t3")
    else:
        sweep(grid_points(int(sys.argv[2]) if len(sys.argv) > 2 else 55), "g2")
