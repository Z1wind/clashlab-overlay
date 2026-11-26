# -*- coding: utf-8 -*-
"""level_visual 改进：收紧裁剪 + 去掉草地/地形像素后再比颜色。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "level_visual.py")
t = open(p, encoding="utf-8").read()

t = t.replace('''def _hist(bgr, mask=None):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], mask, [_H_BINS, _S_BINS, _V_BINS], [0, 180, 0, 256, 0, 256])
    h = cv2.normalize(h, None).flatten()
    return h''',
'''def _hist(bgr, mask=None):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], mask, [_H_BINS, _S_BINS, _V_BINS], [0, 180, 0, 256, 0, 256])
    h = cv2.normalize(h, None).flatten()
    return h


def _trim_mask(bgr, alpha_mask=None):
    """建筑「配色」像素：排除草地/地形绿与过暗阴影，保留金属/宝石色。"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    ok = (S > 55) & (V > 45)
    grass = (H >= 32) & (H <= 90) & (S > 70)          # 草地/树叶绿
    ok = ok & (~grass)
    m = (ok.astype(np.uint8) * 255)
    if alpha_mask is not None:
        m = cv2.bitwise_and(m, alpha_mask)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return m''')

t = t.replace('''        if img.shape[2] == 4:
            alpha = img[:, :, 3]
            bgr = img[:, :, :3]
            bgr = cv2.resize(bgr, (CROP, CROP), interpolation=cv2.INTER_AREA)
            alpha = cv2.resize(alpha, (CROP, CROP), interpolation=cv2.INTER_AREA)
            mask = (alpha > 120).astype(np.uint8) * 255
            if int((mask > 0).sum()) < 40:
                mask = None''',
'''        if img.shape[2] == 4:
            alpha = img[:, :, 3]
            bgr = img[:, :, :3]
            bgr = cv2.resize(bgr, (CROP, CROP), interpolation=cv2.INTER_AREA)
            alpha = cv2.resize(alpha, (CROP, CROP), interpolation=cv2.INTER_AREA)
            am = (alpha > 120).astype(np.uint8) * 255
            mask = _trim_mask(bgr, am)
            if int((mask > 0).sum()) < 40:
                mask = am if int((am > 0).sum()) >= 40 else None''')

t = t.replace('''    half = (int(size) - 1) / 2.0
    src = np.array([[gx - half, gy - half], [gx + half + 1, gy - half],
                    [gx + half + 1, gy + half + 1], [gx - half, gy + half + 1]], np.float32)''',
'''    # 收紧到内圈 72%：少带草地/道路，避免地形颜色干扰
    half = (int(size) - 1) / 2.0
    inner = 0.36 * int(size)
    cx, cy = gx + half, gy + half
    src = np.array([[cx - inner, cy - inner], [cx + inner, cy - inner],
                    [cx + inner, cy + inner], [cx - inner, cy + inner]], np.float32)''')

# estimate：用 trim mask
t = t.replace('''    m = _color_mask(crop)
    if int((m > 0).sum()) < 40:
        m = None
    h = _hist(crop, m)''',
'''    m = _trim_mask(crop)
    if int((m > 0).sum()) < 40:
        m = None
    h = _hist(crop, m)''')

open(p, "w", encoding="utf-8", newline="\n").write(t)
print("level_visual improved")
