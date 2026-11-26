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
QUAD_RE = re.compile(r"quad\s*(?:[（(][^）)]*[）)])?\s*=\s*\[\[[^\]]+\](?:\s*,\s*\[[^\]]+\]){3,}\]")


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


ANN_RE = re.compile(r"^(\d+)_annotated\.json$")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_base_dir(root, name):
    """在 <root>/bases/th*/<name>/ 下找带 base.png 的阵目录。"""
    bases = os.path.join(root, "bases")
    if not os.path.isdir(bases):
        return None
    for th in sorted(os.listdir(bases)):
        d = os.path.join(bases, th, name)
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "base.png")):
            return d
    return None


def _quad_for(base_dir, name, fallback_note=None):
    """quad 优先级：out/annotate/<name>_quad.json > bases/<th>/<name>/layout.json > 传入 note。"""
    root = os.path.dirname(base_dir) if base_dir else None
    override = os.path.join(ROOT_DIR, "out", "annotate", name + "_quad.json")
    if os.path.exists(override):
        try:
            q = json.load(open(override, encoding="utf-8")).get("quad")
            if q:
                return q
        except Exception:
            pass
    if base_dir:
        base_layout = os.path.join(base_dir, "layout.json")
        if os.path.exists(base_layout):
            try:
                q = parse_quad(json.load(open(base_layout, encoding="utf-8")).get("note"))
                if q:
                    return q
            except Exception:
                pass
    return parse_quad(fallback_note)


def load_layouts(paths, root=None):
    """读入 layout/annotation 列表，返回 [(base_name, layout, image_path, calib)]。

    支持两种输入：
    - bases/th16/NN/layout.json（原 layout，图像同目录 base.png）
    - out/annotate/NN_annotated.json（用户标注；图像取 bases/th*/NN/base.png，
      quad 优先 out/annotate/NN_quad.json 覆盖，其次该阵 layout.json，最后用标注文件自带 note）
    """
    from .geo import Calib
    root = root or ROOT_DIR
    out = []
    for p in paths:
        lay = json.load(open(p, encoding="utf-8"))
        m = ANN_RE.match(os.path.basename(p))
        if m:
            name = m.group(1)
            base_dir = _find_base_dir(root, name)
            if not base_dir:
                continue
            img = os.path.join(base_dir, "base.png")
            quad = _quad_for(base_dir, name, lay.get("note"))
        else:
            base_dir = os.path.dirname(os.path.abspath(p))
            name = os.path.basename(base_dir)
            img = os.path.join(base_dir, "base.png")
            quad = _quad_for(base_dir, name, lay.get("note"))
        if not os.path.exists(img) or quad is None:
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
