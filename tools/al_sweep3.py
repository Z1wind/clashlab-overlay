# -*- coding: utf-8 -*-
"""步骤 3：easyocr 标注采集（名称卡片优先，读不准再退到信息面板标题）。

实测（easyocr_check.json）：
  面板标题「亿级兵营」→ 兵营正确（等级段会错）
  名称卡片「建筑-人少屋 / 2级」→ 可模糊匹配
所以：卡片优先（1 次点击 1 张图），模糊匹配不到再用信息面板标题兜底。
"""
import json, os, sys, time, difflib
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import al_drive as d

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label")
CARD = (430, 440, 860, 522)
TITLE = (480, 18, 830, 78)
INFO_BTN = (516, 570)
CLOSE_X = (1131, 48)

NAMES = {
    "多重箭塔": "multi-archer-tower", "弹射加农炮": "ricochet-cannon", "隐形特斯拉": "hidden-tesla",
    "特斯拉电磁塔": "hidden-tesla", "防空火箭": "air-defense", "法师塔": "wizard-tower",
    "炸弹塔": "bomb-tower", "地狱之塔": "inferno-tower", "鹰火炮": "eagle-artillery",
    "投石炮": "scattershot", "空气炮": "air-sweeper", "巨石碑": "monolith", "法术塔": "spell-tower",
    "部落城堡": "clan-castle", "大本营": "town-hall", "加农炮": "cannon", "箭塔": "archer-tower",
    "迫击炮": "mortar", "X连弩": "x-bow", "喷火器": "firespitter",
    "兵营": "other", "城墙": "wall", "建筑工人小屋": "builder-hut", "金矿": "collector-gold",
    "圣水收集器": "collector-elixir", "储金罐": "storage-gold", "圣水瓶": "storage-elixir",
    "暗黑重油罐": "storage-dark", "黑油钻井": "collector-dark", "实验室": "lab",
}
_reader = None


def reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    return _reader


def imread(path):
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)


def ocr_region(img, box, scale=2):
    x0, y0, x1, y1 = box
    reg = img[y0:y1, x0:x1]
    reg = cv2.resize(reg, (reg.shape[1] * scale, reg.shape[0] * scale), interpolation=cv2.INTER_LANCZOS4)
    res = reader().readtext(reg, detail=0, paragraph=False)
    return [t for t in res if t.strip()]


def match_name(lines):
    """模糊匹配：把 OCR 文本里每个 3–5 字窗口与 26 个已知名比相似度，取最高。"""
    text = "".join(ch for ch in "".join(lines) if ord(ch) > 0x2E80)
    best = (0.0, None)
    for name, typ in NAMES.items():
        for i in range(0, max(1, len(text) - len(name) + 1)):
            cand = text[i:i + len(name)]
            r = difflib.SequenceMatcher(None, cand, name).ratio()
            if r > best[0]:
                best = (r, (name, typ))
        if len(text) >= 2:
            r = difflib.SequenceMatcher(None, text, name).ratio()
            if r > best[0]:
                best = (r, (name, typ))
    return best


def probe_point(x, y, save_dir=None, tag=""):
    d.tap(x, y, "sel")
    time.sleep(0.75)
    img = d.shot()
    lines = ocr_region(img, CARD)
    ratio, hit = match_name(lines)
    src = "card"
    if ratio < 0.55:
        # 兜底：打开信息面板读标题
        d.tap(*INFO_BTN, note="info")
        time.sleep(1.2)
        img2 = d.shot()
        lines2 = ocr_region(img2, TITLE, scale=3)
        r2, h2 = match_name(lines2)
        d.tap(*CLOSE_X, note="close")
        time.sleep(0.45)
        if r2 > ratio:
            ratio, hit, lines, src = r2, h2, lines2, "title"
    if save_dir:
        half = 110
        x0, y0 = max(0, x - half), max(0, y - half)
        crop = img[y0:y0 + 2 * half, x0:x0 + 2 * half]
        if crop.shape[0] == 2 * half and crop.shape[1] == 2 * half and hit is not None:
            cv2.imencode(".png", crop)[1].tofile(os.path.join(save_dir, "%s_%d_%d.png" % (tag, x, y)))
    return {"x": x, "y": y, "ratio": round(ratio, 3), "name": hit[0] if hit else None,
            "type": hit[1] if hit else None, "source": src, "lines": lines[:4]}


def grid_points(x0=150, x1=1130, y0=90, y1=520, step=55):
    return [(x, y) for y in range(y0, y1, step) for x in range(x0, x1, step)]


def sweep(points, tag, save_crops=False):
    save_dir = os.path.join(OUT, "sweep3")
    if save_crops:
        os.makedirs(save_dir, exist_ok=True)
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
            rec = probe_point(x, y, save_dir if save_crops else None, tag)
        except Exception as e:
            rec = {"x": x, "y": y, "error": str(e)[:60] and str(e)[:60]}
        results.append(rec)
        if (i + 1) % 20 == 0:
            json.dump(results, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            hit = sum(1 for r in results if r.get("name"))
            print("progress %d/%d hit=%d %.0fs" % (i + 1, len(points), hit, time.time() - t0))
    json.dump(results, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DONE n=%d hit=%d" % (len(results), sum(1 for r in results if r.get("name"))))


if __name__ == "__main__":
    if sys.argv[1] == "test":
        pts = [(890, 380), (640, 300), (500, 250), (300, 200), (760, 430), (700, 200), (950, 300), (560, 480)]
        sweep(pts, "t4", save_crops=True)
    else:
        sweep(grid_points(int(sys.argv[2]) if len(sys.argv) > 2 else 55), "g3")
