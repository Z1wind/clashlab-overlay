# -*- coding: utf-8 -*-
"""游戏自标注：高倍下点建筑 → OCR 名称卡（中文名即标签）→ 存样本。

实测：44px/格 运行时名称卡在点击点右上方，文字大（约 28px 高），easyocr 可读（如「投石炮（1级）」）。
"""
import json, os, sys, re, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import al_drive as d

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label", "game")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "crops"), exist_ok=True)
_reader = None


def reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    return _reader


def ocr_name(img, x, y):
    h, w = img.shape[:2]
    x0, y0 = max(0, x - 320), max(0, y - 300)
    x1, y1 = min(w, x + 320), min(h, y + 160)
    reg = img[y0:y1, x0:x1]
    big = cv2.resize(reg, (reg.shape[1] * 2, reg.shape[0] * 2), interpolation=cv2.INTER_LANCZOS4)
    res = reader().readtext(big, detail=0, paragraph=False)
    return [t for t in res if t.strip()], reg


def canon(lines):
    """从 OCR 文本里取建筑名：形如「投石炮（1级）」或「投石炮(1级)」。"""
    for t in lines:
        t2 = t.replace(" ", "")
        m = re.match(r"^([\u4e00-\u9fffX]{2,8})[（(]\s*\d+\s*级\s*[）)]", t2)
        if m:
            return m.group(1), t2
    for t in lines:
        t2 = t.replace(" ", "")
        m = re.match(r"^([\u4e00-\u9fffX]{2,8})[（(]", t2)
        if m:
            return m.group(1), t2
    return None, (lines[0] if lines else "")


def one(x, y, tag):
    pre = d.shot()
    try:
        d.tap(x, y, "label")
    except RuntimeError as e:
        return {"x": x, "y": y, "error": str(e)[:40]}
    time.sleep(0.75)
    img = d.shot()
    lines, reg = ocr_name(img, x, y)
    name, raw = canon(lines)
    rec = {"x": x, "y": y, "name": name, "raw": raw, "lines": lines[:4]}
    if name:
        half = 150
        cx0, cy0 = max(0, x - half), max(0, y - half)
        crop = img[cy0:cy0 + 2 * half, cx0:cx0 + 2 * half]
        if crop.shape[0] == 300 and crop.shape[1] == 300:
            p = os.path.join(OUT, "crops", "%s_%d_%d.png" % (tag, x, y))
            cv2.imencode(".png", crop)[1].tofile(p)
            rec["crop"] = p
    return rec


def grid(x0=170, x1=1110, y0=110, y1=540, step=90):
    return [(x, y) for y in range(y0, y1, step) for x in range(x0, x1, step)]


def run(points, tag):
    path = os.path.join(OUT, tag + ".json")
    done = {}
    if os.path.exists(path):
        for r in json.load(open(path, encoding="utf-8")):
            done[(r["x"], r["y"])] = r
    out = list(done.values())
    t0 = time.time()
    for i, (x, y) in enumerate(points):
        if (x, y) in done:
            continue
        r = one(x, y, tag)
        out.append(r)
        if (i + 1) % 10 == 0:
            json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            hit = sum(1 for z in out if z.get("name"))
            print("progress %d/%d hit=%d %.0fs" % (i + 1, len(points), hit, time.time() - t0), flush=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DONE n=%d hit=%d" % (len(out), sum(1 for z in out if z.get("name"))))


if __name__ == "__main__":
    if sys.argv[1] == "test":
        pts = [(480, 570), (700, 470), (950, 400), (300, 300), (620, 250), (1050, 220)]
        run(pts, "t_gl")
    else:
        run(grid(int(sys.argv[2]) if len(sys.argv) > 2 else 90), "g_gl")
