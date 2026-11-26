# -*- coding: utf-8 -*-
"""27px 识别模型推理入口：加载 checkpoint + 纯推理。

数据口径（与 clashlab/recog_dataset.py 一致）：
- 输入是 layout 标注 tile 中心、4.5 格窗口反投影出的 96x96 BGR(uint8) 裁剪；
- checkpoint 里存 state_dict + classes + input_size，classes 顺序即输出列顺序。

用法：
    from clashlab.recog_model import load_model, predict_crops
    model = load_model()                 # 默认 models/recog_27px.pt
    probs = predict_crops(crops)         # list[np.ndarray(H,W,3) BGR] -> (N, C) softmax
    probs = model.predict_crops(crops)   # 同一个模型对象复用
"""
from __future__ import annotations

import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CHECKPOINT = os.path.join(ROOT, "models", "recog_27px.pt")
INPUT_SIZE = 96
ARCH = "smallcnn-24-48-96"


class Net(nn.Module):
    """与 tools/train_from_annotations.py 同构的小 CNN（3 个 double-conv 块 → 96 维）。"""

    def __init__(self, ncls: int):
        super().__init__()
        def blk(i, o):
            return nn.Sequential(
                nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True),
                nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3, 24), blk(24, 48), blk(48, 96), nn.AdaptiveAvgPool2d(1))
        self.head = nn.Sequential(nn.Flatten(), nn.Dropout(0.35), nn.Linear(96, ncls))

    def forward(self, x):
        return self.head(self.f(x))


def _to_batch(images):
    """把 list[HxWx3] / ndarray(N,H,W,3) / 单张 HxWx3 统一成 (N,H,W,3) uint8 的 batch。"""
    if isinstance(images, np.ndarray) and images.ndim == 3:
        images = [images]
    arr = np.asarray(images, dtype=np.uint8)
    if arr.ndim == 3:
        arr = arr[None, ...]
    if arr.ndim != 4 or arr.shape[-1] != 3:
        raise ValueError("predict_crops 需要 (N,H,W,3) BGR uint8，实际 %r" % (arr.shape,))
    if len(arr) == 0:
        raise ValueError("predict_crops 收到空 batch")
    return arr


def _preprocess(batch, input_size):
    """BGR uint8 (N,H,W,3) → RGB float32 (N,3,size,size) ∈ [0,1]；尺寸不符时双线性缩放。"""
    x = torch.from_numpy(np.ascontiguousarray(batch[..., ::-1].astype(np.float32) / 255.0))
    x = x.permute(0, 3, 1, 2).contiguous()
    if x.shape[-1] != input_size or x.shape[-2] != input_size:
        x = F.interpolate(x, size=(input_size, input_size), mode="bilinear", align_corners=False)
    return x


class Recognizer:
    """已加载的模型：net + classes + input_size，全部推理放在 eval/no_grad 下。"""

    def __init__(self, net, classes, input_size, checkpoint_path=None, meta=None):
        self.net = net
        self.classes = list(classes)
        self.input_size = int(input_size)
        self.checkpoint_path = checkpoint_path
        self.meta = dict(meta or {})

    def predict_crops(self, images) -> np.ndarray:
        """images: list[np.ndarray(H,W,3) BGR uint8] 或 (N,H,W,3) → 概率 (N, C)。"""
        batch = _to_batch(images)
        x = _preprocess(batch, self.input_size)
        self.net.eval()
        with torch.no_grad():
            logits = self.net(x)
            probs = F.softmax(logits, dim=1)
        return probs.cpu().numpy().astype(np.float32)

    def __repr__(self):
        return "Recognizer(classes=%d, input_size=%d, path=%r)" % (
            len(self.classes), self.input_size, self.checkpoint_path)


_DEFAULT_CACHE = {}


def load_model(path=None, device="cpu") -> Recognizer:
    """加载 checkpoint，返回 Recognizer。path 缺省用 models/recog_27px.pt。"""
    path = os.path.abspath(path or DEFAULT_CHECKPOINT)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "checkpoint 不存在：%s（先跑 python tools/train_save_model.py）" % path)
    ckpt = torch.load(path, map_location=device, weights_only=True)
    for key in ("state_dict", "classes", "input_size"):
        if key not in ckpt:
            raise ValueError("checkpoint 缺字段 %r：%s" % (key, path))
    classes = [str(c) for c in ckpt["classes"]]
    net = Net(len(classes))
    net.load_state_dict(ckpt["state_dict"])
    net.to(device)
    net.eval()
    meta = {k: v for k, v in ckpt.items() if k not in ("state_dict", "classes")}
    return Recognizer(net, classes, int(ckpt["input_size"]), checkpoint_path=path, meta=meta)


def save_model(net, classes, path, input_size=INPUT_SIZE, **meta):
    """按统一 schema 落盘：state_dict + classes + input_size + arch + 自定义 meta。"""
    payload = {
        "state_dict": net.state_dict(),
        "classes": [str(c) for c in classes],
        "input_size": int(input_size),
        "arch": ARCH,
        "normalize": "bgr_uint8_to_rgb_0_1",
    }
    payload.update(meta)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    torch.save(payload, path)
    return payload


def get_default_model() -> Recognizer:
    """按 checkpoint 路径缓存默认模型（mtime 变化则重新加载）。"""
    path = os.path.abspath(DEFAULT_CHECKPOINT)
    mtime = os.path.getmtime(path) if os.path.exists(path) else -1.0
    hit = _DEFAULT_CACHE.get(path)
    if hit is None or hit[0] != mtime:
        model = load_model(path)
        _DEFAULT_CACHE[path] = (mtime, model)
        return model
    return hit[1]


def predict_crops(images, model=None) -> np.ndarray:
    """模块级便捷入口：用默认 checkpoint 推理。"""
    return (model or get_default_model()).predict_crops(images)
