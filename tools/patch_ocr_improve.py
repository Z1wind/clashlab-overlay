# -*- coding: utf-8 -*-
"""改进 OCR：紧裁剪 + 3x 放大 + 灰度增强；解析合并行「16. 名字」。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "ocr_screen.py")
t = open(p, encoding="utf-8").read()

t = t.replace('TOP_CROP = (0.0, 0.0, 0.60, 0.16)',
              'TOP_CROP = (0.0, 0.0, 0.42, 0.13)')
t = t.replace('''def _parse_lines(lines):''', '''def _strip_level(text):
    """把「16. MH Tipu」拆成 (level, name)；拆不出返回 (None, 原文)。"""
    m = re.match(r"^\\s*(\\d{1,2})\\s*[.．、]\\s*(.+)$", text)
    if m:
        return m.group(1) + ".", m.group(2).strip()
    m = re.match(r"^\\s*(\\d{1,2})\\s*本\\s*(.+)$", text)
    if m:
        return m.group(1) + "本", m.group(2).strip()
    return None, text


def _parse_lines(lines):''')
t = t.replace('''    level = None
    rest = []
    for t in texts[:4]:
        m = _LEVEL_RE.match(t)
        if m and level is None:
            level = t
            continue
        if _BADGE_RE.match(t) and level is None:
            level = t
            continue
        rest.append(t)''',
'''    level = None
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
        rest.append(raw)''')

t = t.replace('''def ocr_lines(img_bgr, crop=TOP_CROP):
    """对图片（BGR ndarray）做 OCR，返回 [{"text","score","box"}]。"""
    from rapidocr_onnxruntime import RapidOCR  # 延迟导入：没装也能 import 本模块
    import cv2
    h, w = img_bgr.shape[:2]
    x0, y0, x1, y1 = crop
    sub = img_bgr[int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    engine = RapidOCR()
    res, _ = engine(sub)''',
'''def ocr_lines(img_bgr, crop=TOP_CROP, scale=3):
    """对图片（BGR ndarray）做 OCR，返回 [{"text","score","box"}]。"""
    from rapidocr_onnxruntime import RapidOCR  # 延迟导入：没装也能 import 本模块
    import cv2
    h, w = img_bgr.shape[:2]
    x0, y0, x1, y1 = crop
    sub = img_bgr[int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    if scale and scale != 1:
        sub = cv2.resize(sub, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    engine = RapidOCR()
    res, _ = engine(sub)''')

open(p, "w", encoding="utf-8", newline="\n").write(t)
print("ocr improved")
