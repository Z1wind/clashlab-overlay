# -*- coding: utf-8 -*-
"""用「配色/纹理特征」估计建筑等级。

思路：assets/coc/buildings/<type>/level-N.png 是逐级美术资源；把阵图里该建筑的
透视 crop warp 成正方形，和同一类型每一级 sprite 比颜色直方图（HSV，加权饱和像素），
取最接近的等级。没有人工等级标签，所以输出的是 level_est + confidence，供人工复核。
"""
from __future__ import annotations

import os
import glob
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "assets", "coc", "buildings")
CROP = 72
_H_BINS, _S_BINS, _V_BINS = 24, 8, 4
_cache = {}


def _hist(bgr, mask=None):
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
    return m


def _color_mask(bgr):
    """只保留「有颜色/有亮度」的像素：过滤草地、阴影、灰底。"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    s, v = hsv[:, :, 1], hsv[:, :, 2]
    m = ((s > 45) & (v > 35)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return m


def templates(btype):
    """返回 [(level, hist)]；只缓存带 alpha 的 sprite 的有效像素。"""
    key = str(btype)
    if key in _cache:
        return _cache[key]
    out = []
    d = os.path.join(ART, key)
    for p in sorted(glob.glob(os.path.join(d, "level-*.png"))):
        try:
            lv = int(os.path.basename(p).split("-")[1].split(".")[0])
        except Exception:
            continue
        img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            continue
        if img.shape[2] == 4:
            alpha = img[:, :, 3]
            bgr = img[:, :, :3]
            bgr = cv2.resize(bgr, (CROP, CROP), interpolation=cv2.INTER_AREA)
            alpha = cv2.resize(alpha, (CROP, CROP), interpolation=cv2.INTER_AREA)
            am = (alpha > 120).astype(np.uint8) * 255
            mask = _trim_mask(bgr, am)
            if int((mask > 0).sum()) < 40:
                mask = am if int((am > 0).sum()) >= 40 else None
        else:
            bgr = cv2.resize(img, (CROP, CROP), interpolation=cv2.INTER_AREA)
            mask = _color_mask(bgr)
        out.append((lv, _hist(bgr, mask)))
    _cache[key] = out
    return out


def crop_building(base_bgr, calib, tile, size):
    """把 size×size 的 tile 区块从透视阵图 warp 成 CROP×CROP 正方形。"""
    n = int(getattr(calib, "n", 44) or 44)
    gx, gy = float(tile[0]), float(tile[1])
    # 收紧到内圈 72%：少带草地/道路，避免地形颜色干扰
    half = (int(size) - 1) / 2.0
    inner = 0.36 * int(size)
    cx, cy = gx + half, gy + half
    src = np.array([[cx - inner, cy - inner], [cx + inner, cy - inner],
                    [cx + inner, cy + inner], [cx - inner, cy + inner]], np.float32)
    pts = np.array([calib.tile_to_px(p[0], p[1]) for p in src], np.float32)
    dst = np.array([[0, 0], [CROP, 0], [CROP, CROP], [0, CROP]], np.float32)
    M = cv2.getPerspectiveTransform(pts, dst)
    return cv2.warpPerspective(base_bgr, M, (CROP, CROP), flags=cv2.INTER_AREA)


def _dist(a, b):
    """直方图距离（0..2，越小越像）。"""
    return float(np.sum(np.abs(a - b)))


def estimate(crop, btype, topk=3):
    """返回 {'level','confidence','top':[(level,dist)]}；无素材时 level=None。"""
    tpls = templates(btype)
    if not tpls:
        return {"level": None, "confidence": 0.0, "top": []}
    m = _trim_mask(crop)
    if int((m > 0).sum()) < 40:
        m = None
    h = _hist(crop, m)
    scored = sorted(((_dist(h, th), lv) for lv, th in tpls), key=lambda x: x[0])
    best_d, best_lv = scored[0]
    second_d = scored[1][0] if len(scored) > 1 else best_d + 1e-6
    conf = max(0.0, min(1.0, (second_d - best_d) / max(second_d, 1e-6)))
    return {"level": int(best_lv), "confidence": round(conf, 3),
            "top": [{"level": int(lv), "dist": round(float(d), 4)} for d, lv in scored[:topk]]}
