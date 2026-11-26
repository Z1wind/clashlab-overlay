# -*- coding: utf-8 -*-
"""游戏画面 OCR：从对战界面顶部读出「对手名字 / 部落名」。

后端：RapidOCR（onnxruntime，离线，支持中英）。纯解析函数 _parse_lines 可单测，
不依赖 OCR 引擎。
"""
from __future__ import annotations

import re

# 顶部区域的相对裁剪（对战界面：等级+名字+部落名在左上）
TOP_CROP = (0.0, 0.0, 0.42, 0.13)
_LEVEL_RE = re.compile(r"^\s*(?:\d{1,2}\s*本|Lv\.?\s*\d{1,2}|\d{1,3}\s*[.．、]?)\s*$")
_BADGE_RE = re.compile(r"^\s*\d{1,3}\s*$")


def _clean(s):
    return re.sub(r"\s+", " ", str(s or "")).strip(" .·|_-")


def _strip_level(text):
    """把「16. MH Tipu」拆成 (level, name)；拆不出返回 (None, 原文)。"""
    m = re.match(r"^\s*(\d{1,2})\s*[.．、]\s*(.+)$", text)
    if m:
        return m.group(1) + ".", m.group(2).strip()
    m = re.match(r"^\s*(\d{1,2})\s*本\s*(.+)$", text)
    if m:
        return m.group(1) + "本", m.group(2).strip()
    return None, text


def _parse_lines(lines):
    """解析 OCR 文本行 -> {level, name, clan}。

    规则（对战界面顶部）：
    - 首行常见「15.」是对方大本等级；
    - 名字通常是第二行（可能带特殊符号/字母数字混合）；
    - 名字下面一行是部落名（可含空格）。
    lines: [{"text":..., "score":...}] 或 [str]
    """
    texts = []
    for ln in lines:
        t = ln.get("text") if isinstance(ln, dict) else ln
        t = _clean(t)
        if t:
            texts.append(t)
    level = None
    rest = []
    for raw in texts[:5]:
        lv, name = _strip_level(raw)
        if lv is not None and level is None:
            level = lv
            if name:
                rest.append(name)
            continue
        if _LEVEL_RE.match(raw) and level is None:
            level = raw
            continue
        if _BADGE_RE.match(raw) and level is None:
            level = raw
            continue
        rest.append(raw)
    # 纯数字行（等级徽章/胜场数）不当作名字/部落
    rest = [x for x in rest if not re.match(r"^\d{1,3}$", x)]
    name = rest[0] if rest else None
    clan = rest[1] if len(rest) > 1 else None
    return {"level": level, "name": name, "clan": clan}


def ocr_lines(img_bgr, crop=TOP_CROP, scale=3):
    """对图片（BGR ndarray）做 OCR，返回 [{"text","score","box"}]。"""
    from rapidocr_onnxruntime import RapidOCR  # 延迟导入：没装也能 import 本模块
    import cv2
    h, w = img_bgr.shape[:2]
    x0, y0, x1, y1 = crop
    sub = img_bgr[int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    if scale and scale != 1:
        sub = cv2.resize(sub, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    engine = RapidOCR()
    res, _ = engine(sub)
    out = []
    for item in res or []:
        box, text, score = item[0], item[1], item[2]
        out.append({"text": str(text), "score": round(float(score), 3), "box": box})
    return out


def read_opponent(img_bgr):
    """OCR + 解析：返回 {level,name,clan,lines}；失败抛 RuntimeError。"""
    lines = ocr_lines(img_bgr)
    parsed = _parse_lines(lines)
    parsed["lines"] = [{"text": l["text"], "score": l["score"]} for l in lines]
    return parsed
