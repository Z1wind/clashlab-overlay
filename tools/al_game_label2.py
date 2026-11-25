# -*- coding: utf-8 -*-
"""游戏自标注 v2：按画面里的「非草地」像素撒点（提高点中建筑的比例），点建筑 → OCR 名称。

标签来源 = 游戏自己显示的名称（中文），不经我判类。
"""
import json, os, sys, re, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import al_drive as d

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label", "game")
os.makedirs(os.path.join(OUT, "crops"), exist_ok=True)
_reader = None


def reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
    return _reader


UI_EXCLUDE = [(0, 0, 175, 720), (0, 0, 400, 110), (0, 520, 1280, 720), (1080, 0, 1280, 520)]


def in_ui(x, y):
    for x0, y0, x1, y1 in UI_EXCLUDE:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False


def candidate_points(img, step=45):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    grass = (h >= 30) & (h <= 95) & (s > 45) & (v > 35)
    water = (h >= 95) & (h <= 135) & (s > 60) & (v > 40)
    mask = (~(grass | water)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    pts = []
    for y in range(110, 520, step):
        for x in range(175, 1080, step):
            if in_ui(x, y):
                continue
            y0, y1 = max(0, y - 8), min(img.shape[0], y + 8)
            x0, x1 = max(0, x - 8), min(img.shape[1], x + 8)
            if mask[y0:y1, x0:x1].mean() > 0.5:
                pts.append((x, y))
    return pts


def ocr_name(img, x, y):
    h, w = img.shape[:2]
    x0, y0 = max(0, x - 340), max(0, y - 320)
    x1, y1 = min(w, x + 340), min(h, y + 320)
    reg = img[y0:y1, x0:x1]
    if reg.size == 0:
        return [], reg
    big = cv2.resize(reg, (int(reg.shape[1] * 1.8), int(reg.shape[0] * 1.8)), interpolation=cv2.INTER_LANCZOS4)
    res = reader().readtext(big, detail=0, paragraph=False)
    return [t for t in res if t.strip()], reg


def canon(lines):
    best = None
    for t in lines:
        t2 = t.replace(" ", "")
        m = re.search(r"([\u4e00-\u9fffX]{2,8})[（(]\s*\d+\s*级", t2)
        if m:
            return m.group(1), t2
        m2 = re.search(r"([\u4e00-\u9fffX]{2,8})[（(]", t2)
        if m2 and best is None:
            best = (m2.group(1), t2)
    return best if best else (None, (lines[0] if lines else ""))


def one(x, y, tag):
    try:
        d.tap(x, y, "glabel")
    except RuntimeError as e:
        return {"x": x, "y": y, "error": str(e)[:40]}
    time.sleep(0.7)
    img = d.shot()
    lines, reg = ocr_name(img, x, y)
    name, raw = canon(lines)
    rec = {"x": x, "y": y, "name": name, "raw": raw}
    if name:
        half = 150
        cx0, cy0 = max(0, x - half), max(0, y - half)
        crop = img[cy0:cy0 + 2 * half, cx0:cx0 + 2 * half]
        if crop.shape[0] == 300 and crop.shape[1] == 300:
            p = os.path.join(OUT, "crops", "%s_%d_%d.png" % (tag, x, y))
            cv2.imencode(".png", crop)[1].tofile(p)
            rec["crop"] = os.path.basename(p)
    return rec


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "g1"
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    img = d.shot()
    pts = candidate_points(img, step)
    print("candidate points=%d" % len(pts), flush=True)
    path = os.path.join(OUT, tag + ".json")
    done = set()
    out = []
    if os.path.exists(path):
        out = json.load(open(path, encoding="utf-8"))
        done = {(r["x"], r["y"]) for r in out}
    t0 = time.time()
    for i, (x, y) in enumerate(pts):
        if (x, y) in done:
            continue
        out.append(one(x, y, tag))
        if (i + 1) % 15 == 0:
            json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            hit = sum(1 for z in out if z.get("name"))
            print("progress %d/%d hit=%d %.0fs" % (i + 1, len(pts), hit, time.time() - t0), flush=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DONE n=%d hit=%d" % (len(out), sum(1 for z in out if z.get("name"))))


main()
