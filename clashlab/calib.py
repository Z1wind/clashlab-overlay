# -*- coding: utf-8 -*-
"""村庄菱形自校准（snap 专用）。

不套旧标定参数：从草地掩膜最大轮廓取菱形四角，失败回退 vision.detect_boundary。
坐标换算仍只走 geo.Calib，本模块只负责求 quad。
"""
import cv2
import numpy as np

from . import vision
from .geo import Calib


def _order_diamond(pts):
    """四角按 顶/右/底/左 排序（相对质心角度）。"""
    pts = np.asarray(pts, dtype=np.float32)
    c = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    order = np.argsort(ang)
    pts = pts[order]
    # 找最上点为顶，顺时针：顶->右->底->左
    top_i = int(np.argmin(pts[:, 1]))
    pts = np.roll(pts, -top_i, axis=0)
    return pts


def detect_village_quad(frame, grid_n=44):
    """返回 (Calib|None, meta dict)。草地轮廓法为主，detect_boundary 兜底。"""
    fh, fw = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    # 草地：绿相、中饱和、中亮；排除暗森林与 UI 条
    grass = ((h >= 28) & (h <= 98) & (s >= 32) & (v >= 78) & (v <= 228)).astype(np.uint8) * 255
    ui = np.zeros((fh, fw), np.uint8)
    ui[int(fh * 0.10):int(fh * 0.90), int(fw * 0.08):int(fw * 0.93)] = 255
    m = cv2.bitwise_and(grass, ui)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    meta = {"method": "grass_contour"}
    quad = None
    if n > 1:
        bi = max(range(1, n), key=lambda i: stats[i, 4])
        comp = (lab == bi).astype(np.uint8) * 255
        comp = cv2.morphologyEx(comp, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
        contours, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.05 * peri, True)
            if len(approx) == 4:
                quad = approx.reshape(4, 2).astype(np.float32)
            else:
                box = cv2.boxPoints(cv2.minAreaRect(c))
                quad = box.astype(np.float32)
            quad = _order_diamond(quad)
            meta["quad"] = np.round(quad, 1).tolist()
    if quad is None:
        calib, bmeta = vision.detect_boundary(frame, grid_n=grid_n)
        meta["method"] = "detect_boundary"
        meta["source"] = (bmeta or {}).get("source")
        meta["confidence"] = (bmeta or {}).get("confidence")
        return calib, meta
    return Calib.from_quad(quad, n=grid_n), meta


def draw_grid(frame, calib, color=(0, 255, 0), step=1):
    """在帧上画网格线（grid_check 用）。"""
    vis = frame.copy()
    n = calib.n
    for i in range(0, n + 1, step):
        p0 = calib.tile_to_px(i, 0)
        p1 = calib.tile_to_px(i, n)
        q0 = calib.tile_to_px(0, i)
        q1 = calib.tile_to_px(n, i)
        cv2.line(vis, tuple(map(int, p0)), tuple(map(int, p1)), color, 1)
        cv2.line(vis, tuple(map(int, q0)), tuple(map(int, q1)), (255, 128, 0), 1)
    return vis
