# -*- coding: utf-8 -*-
"""从阵图预测 44×44 地图四角（上/右/下/左）的回归模型。

输入：BGR 图像（内部 resize 到固定尺寸）；输出：4 个角点的像素坐标。
用途：import_base 草地检测失败时的兜底标定。
"""
from __future__ import annotations

import json
import os

import numpy as np

try:
    import torch
    import torch.nn as nn
except Exception:  # pragma: no cover
    torch = None
    nn = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CKPT = os.path.join(ROOT, "models", "quad_model.pt")
INPUT_W, INPUT_H = 320, 180


if nn is not None:
    class QuadNet(nn.Module):
        def __init__(self):
            super().__init__()
            def blk(i, o):
                return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True),
                                     nn.MaxPool2d(2))
            self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), blk(96, 128), nn.AdaptiveAvgPool2d(1))
            self.head = nn.Sequential(nn.Flatten(), nn.Dropout(0.2), nn.Linear(128, 8))

        def forward(self, x):
            return torch.sigmoid(self.head(self.f(x)))
else:  # pragma: no cover
    class QuadNet:  # type: ignore
        def __init__(self):
            raise ImportError("torch 未安装，四角模型不可用")


def _prep(img_bgr):
    import cv2
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (INPUT_W, INPUT_H), interpolation=cv2.INTER_AREA)
    x = rgb.astype(np.float32) / 255.0
    return np.transpose(x, (2, 0, 1))


class QuadModel:
    def __init__(self, state, input_size=(INPUT_W, INPUT_H)):
        self.net = QuadNet()
        self.net.load_state_dict(state)
        self.net.eval()
        self.input_size = tuple(input_size)

    def predict(self, img_bgr):
        """返回 [[x,y]×4]（上/右/下/左，像素坐标）。"""
        with torch.no_grad():
            t = torch.from_numpy(np.stack([_prep(img_bgr)])).float()
            out = self.net(t)[0].numpy().reshape(4, 2)
        w, h = img_bgr.shape[1], img_bgr.shape[0]
        return [[float(out[i][0] * w), float(out[i][1] * h)] for i in range(4)]


def load_model(path=None):
    if torch is None:
        raise ImportError("torch 未安装")
    p = path or CKPT
    if not os.path.exists(p):
        raise FileNotFoundError(p)
    ckpt = torch.load(p, map_location="cpu", weights_only=False)
    return QuadModel(ckpt["state_dict"], ckpt.get("input_size", (INPUT_W, INPUT_H)))
