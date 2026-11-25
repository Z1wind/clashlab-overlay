# -*- coding: utf-8 -*-
"""三路独立分割提案（snap 专用），不依赖模板也必须出框。

通道：
1. 颜色：非草地/非地面的饱和构件（暖/紫/亮/深暗）；
2. 纹理：局部方差高于邻域的团块；
3. 边缘：Canny 密度连通域。
墙（薄长构件）单独一路返回，不与建筑混并，避免墙块淹没建筑候选。

阈值写死、无随机，保证同图两跑逐字节一致。
"""
import cv2
import numpy as np

UI_TOP, UI_BOTTOM, UI_LEFT, UI_RIGHT = 0.09, 0.885, 0.10, 0.915


def _ui_mask(shape):
    h, w = shape[:2]
    m = np.zeros((h, w), np.uint8)
    m[int(h * UI_TOP):int(h * UI_BOTTOM), int(w * UI_LEFT):int(w * UI_RIGHT)] = 255
    return m


def _color_channel(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    warm = (s > 55) & ((h < 18) | (h > 165))
    bright = v > 198
    purple = (h >= 125) & (h <= 162) & (s > 55)
    dark = (v < 105) & (s > 25)
    # 草地/洞穴蓝地不计入建筑颜色
    grass = (h >= 28) & (h <= 98) & (s >= 32)
    blue = (h >= 95) & (h <= 135)
    fg = (warm | bright | purple | dark) & ~(grass | blue)
    return (fg.astype(np.uint8)) * 255


def _texture_channel(frame, k=15):
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    mu = cv2.blur(g, (k, k))
    mu2 = cv2.blur(g * g, (k, k))
    std = np.sqrt(np.maximum(mu2 - mu * mu, 0.0))
    return cv2.normalize(std, None, 0, 255, cv2.NORM_MINMAX)


def _edge_channel(frame):
    edges = cv2.Canny(frame, 40, 120)
    return cv2.dilate(edges, np.ones((5, 5), np.uint8))


def proposal_masks(frame):
    """返回 (building_mask, wall_mask)。"""
    ui = _ui_mask(frame.shape)
    color = _color_channel(frame)
    tex = _texture_channel(frame)
    edge = _edge_channel(frame)
    bm = ((color > 0) | (tex > 120) | (edge > 0)).astype(np.uint8) * 255
    bm = cv2.bitwise_and(bm, ui)
    bm = cv2.morphologyEx(bm, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    bm = cv2.morphologyEx(bm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    wall = cv2.bitwise_and(edge, ui)
    return bm, wall


def extract_blobs(mask, min_px=10, max_area=5200, max_aspect=3.2):
    """连通域 → 建筑候选框；返回 [{box,area,fill}] 按面积降序。
    先腐蚀去粘连，避免三通道合并成巨块被整体过滤。"""
    er = cv2.erode(mask, np.ones((5, 5), np.uint8), iterations=1)
    n, _l, stats, _c = cv2.connectedComponentsWithStats(er, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 90 or area > max_area:
            continue
        if w < min_px or h < min_px:
            continue
        if w / max(h, 1) > max_aspect or h / max(w, 1) > max_aspect:
            continue
        fill = float(area) / float(w * h)
        if fill < 0.12:
            continue
        out.append({"box": (int(x), int(y), int(w), int(h)),
                    "area": int(area), "fill": round(fill, 3)})
    out.sort(key=lambda d: -d["area"])
    return out


def cell_proposal(frame, tile_px, roi=(0.13, 0.13, 0.89, 0.87), keep_pct=65):
    """边缘密度格提案：网格滑动打分，高于分位的格聚类成框。返回 [{box,area,fill}]。"""
    fh, fw = frame.shape[:2]
    edges = _edge_channel(frame)
    cs = max(int(tile_px * 1.5), 18)
    step = max(cs // 2, 9)
    rx0, ry0, rx1, ry1 = int(fw * roi[0]), int(fh * roi[1]), int(fw * roi[2]), int(fh * roi[3])
    scores = []
    cells = []
    for gy in range(ry0, ry1, step):
        for gx in range(rx0, rx1, step):
            sc = int((edges[gy:gy + cs, gx:gx + cs] > 0).sum())
            scores.append(sc)
            cells.append((gx, gy, sc))
    if not scores:
        return []
    thr = float(np.percentile(scores, keep_pct))
    keep = np.zeros((fh // cs + 2, fw // cs + 2), np.uint8)
    for gx, gy, sc in cells:
        if sc >= max(thr, 4):
            keep[gy // cs, gx // cs] = 255
    keep = cv2.dilate(keep, np.ones((3, 3), np.uint8))
    n, _l, stats, _c = cv2.connectedComponentsWithStats(keep, 8)
    out = []
    for i in range(1, n):
        r, c, rr, cc, area = stats[i]
        x0, y0 = c * cs, r * cs
        out.append({"box": (x0, y0, cc * cs, rr * cs), "area": int(area * cs * cs // 4),
                    "fill": 0.3})
    return out


def extract_walls(wall_mask, min_len=24):
    """薄长构件（墙线）单独提取，不进建筑候选。"""
    n, _l, stats, _c = cv2.connectedComponentsWithStats(wall_mask, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        long_side, short_side = max(w, h), min(w, h)
        if long_side < min_len or short_side > 18:
            continue
        if long_side / max(short_side, 1) < 3.5:
            continue
        out.append({"box": (int(x), int(y), int(w), int(h)), "area": int(area)})
    return out
