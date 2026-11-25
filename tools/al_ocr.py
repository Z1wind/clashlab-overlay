# -*- coding: utf-8 -*-
"""OCR + 建筑名模糊匹配 + 弹窗定位（自动标注核心件）。

要点（实测得出）：
- 全屏 OCR 会漏掉小字弹窗，必须先把弹窗区域裁出来放大再 OCR；
- Windows OCR 对游戏描边字有字符级误读（加→力/-），所以用「两字关键词子串」+ 编辑距离兜底。
"""
import json, sys, time
import numpy as np, cv2
from PIL import Image, ImageOps
import winocr

# 关键词 → type。按危险程度排：多字词先匹配，避免「加农炮」把「弹射加农炮」吃掉
PATTERNS = [
    ("弹射", "ricochet-cannon"),
    ("多重", "multi-archer-tower"),
    ("特斯拉", "hidden-tesla"),
    ("防空", "air-defense"),
    ("法师", "wizard-tower"),
    ("炸弹", "bomb-tower"),
    ("地狱", "inferno-tower"),
    ("鹰火", "eagle-artillery"),
    ("投石", "scattershot"),
    ("空气炮", "air-sweeper"),
    ("巨石", "monolith"),
    ("法术", "spell-tower"),
    ("城堡", "clan-castle"),
    ("大本", "town-hall"),
    ("本营", "town-hall"),
    ("农炮", "cannon"),
    ("箭塔", "archer-tower"),
    ("迫击", "mortar"),
    ("击炮", "mortar"),
    ("连弩", "x-bow"),
    ("喷火", "firespitter"),
]

CJK = "".join(chr(c) for c in range(0x4E00, 0x9FFF))


def ocr(img, lang="zh-Hans"):
    return winocr.recognize_pil_sync(img, lang)


def clean(text):
    return "".join(ch for ch in text if ch in CJK)


def classify(text):
    s = clean(text)
    if s == "":
        return None, None
    for kw, typ in PATTERNS:
        if kw in s:
            return typ, kw
    # 兜底：允许一个字符错（取 2 字窗口做近似）
    for kw, typ in PATTERNS:
        for i in range(0, max(1, len(kw) - 1)):
            w = kw[i:i + 2]
            if len(w) < 2:
                continue
            for j in range(0, max(1, len(s) - 1)):
                cand = s[j:j + 2]
                if len(cand) == 2 and sum(a != b for a, b in zip(cand, w)) <= 1:
                    return typ, "~" + w
    return None, None


def preprocess(region_bgr):
    """放大 3 倍 + 灰度 + 自动对比度，让描边字更容易被 OCR 认。"""
    h, w = region_bgr.shape[:2]
    if w < 40 or h < 10:
        return None
    g = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)
    g = cv2.normalize(g, None, 0, 255, cv2.NORM_MINMAX)
    return Image.fromarray(g).convert("RGB")


def changed_box(pre, post, min_area=1500):
    """两张全屏截图之间「出现内容」的包围盒（弹窗/箭头/卡片）。"""
    d = cv2.absdiff(pre, post)
    g = cv2.cvtColor(d, cv2.COLOR_BGR2GRAY)
    _, m = cv2.threshold(g, 25, 255, cv2.THRESH_BINARY)
    m = cv2.dilate(m, np.ones((9, 9), np.uint8), iterations=2)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    best = None
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if a < min_area:
            continue
        if best is None or a > best[4]:
            best = (x, y, w, h, a)
    return best


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "text":
        img = Image.open(sys.argv[2]).convert("RGB")
        res = ocr(img)
        lines = [l.get("text", "") for l in res.get("lines", [])]
        typ, kw = classify(" ".join(lines))
        payload = {"lines": lines, "type": typ, "kw": kw}
        json.dump(payload, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("type=", typ, "kw=", kw)
