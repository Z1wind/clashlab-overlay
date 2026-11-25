# -*- coding: utf-8 -*-
"""从 layout.json（含 quad）构建 27px 识别数据集；供「用标注学习」的流水线使用。

layout.json 的 note 字段含 quad=[[x,y]×4]（base.png 原图像素），
用 clashlab.geo.Calib.from_quad 反投影出 44×44 网格，再按建筑 tile 取 4.5 格窗口（96×96）。
"""
from __future__ import annotations

import json
import os
import re

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

GRID = 44
S = 24            # 反投影后每 tile 像素
WIN_T = 4.5       # crop 边长（tile）
OUT_SIZE = 96     # 供 CNN 的方形输入边长
QUAD_RE = re.compile(r"quad\s*=\s*\[\[[^\]]+\](?:\s*,\s*\[[^\]]+\]){3,}\]")


def parse_quad(note):
    """从 note 文本里取 quad=[[...],[...],[...],[...]]；失败返回 None。"""
    if not note:
        return None
    m = QUAD_RE.search(note)
    if not m:
        return None
    try:
        return json.loads(m.group(0).split("=", 1)[1])
    except Exception:
        return None


def read_img(path):
    if cv2 is None:
        raise RuntimeError("opencv required")
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)


def crop_for_tile(frame, calib, tile, win_t=WIN_T, size=OUT_SIZE):
    w = int(round(win_t * S))
    tx, ty = float(tile[0]), float(tile[1])
    K = calib.H @ np.array([[1.0 / S, 0, tx - win_t / 2.0], [0, 1.0 / S, ty - win_t / 2.0], [0, 0, 1]])
    crop = cv2.warpPerspective(frame, np.linalg.inv(K), (w, w), flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_REPLICATE)
    return cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)


def load_layouts(paths):
    """读入 layout.json 列表，返回 [(base_name, layout, image_path)]。"""
    from .geo import Calib
    out = []
    for p in paths:
        lay = json.load(open(p, encoding="utf-8"))
        base_dir = os.path.dirname(os.path.abspath(p))
        name = os.path.basename(base_dir)
        img = os.path.join(base_dir, "base.png")
        if not os.path.exists(img):
            continue
        quad = parse_quad(lay.get("note"))
        if quad is None:
            continue
        calib = Calib.from_quad(quad, n=int(lay.get("grid", GRID)))
        out.append((name, lay, img, calib))
    return out


def build_dataset(paths):
    """返回 (crops[BGR uint8], labels[str], base_names[str])。"""
    crops, labels, bases = [], [], []
    for name, lay, img, calib in load_layouts(paths):
        frame = read_img(img)
        for b in lay.get("buildings") or []:
            t = b.get("tile")
            if not t:
                continue
            crops.append(crop_for_tile(frame, calib, t))
            labels.append(str(b.get("type")))
            bases.append(name)
    return crops, labels, bases
