# -*- coding: utf-8 -*-
"""从真实截图采样「非建筑」背景负样本（村外岩石/草地/水），用于建筑门控训练。"""
import glob, json, os, random, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "datasets", "bg_negatives")
os.makedirs(OUT, exist_ok=True)
random.seed(7); np.random.seed(7)
S = 96
SHOTS = []
for pat in ("out/live/*.png", "out/live/scouts/*.png"):
    SHOTS += glob.glob(os.path.join(BASE, pat))
SHOTS = [p for p in SHOTS if os.path.getsize(p) > 200000]
print("screenshots:", len(SHOTS))
crops = []
for p in SHOTS:
    img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    if img is None or min(img.shape[:2]) < 200:
        continue
    h, w = img.shape[:2]
    # 只从边缘带采样（避开中央基地）
    for _ in range(60):
        side = random.randint(0, 3)
        if side == 0:   x, y = random.randint(0, max(0, w - S)), random.randint(0, max(0, int(h * 0.12)))
        elif side == 1: x, y = random.randint(0, max(0, w - S)), random.randint(int(h * 0.88), max(int(h * 0.88), h - S))
        elif side == 2: x, y = random.randint(0, max(0, int(w * 0.12))), random.randint(0, max(0, h - S))
        else:           x, y = random.randint(int(w * 0.88), max(int(w * 0.88), w - S)), random.randint(0, max(0, h - S))
        crop = img[y:y + S, x:x + S]
        if crop.shape[:2] != (S, S):
            continue
        g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        if cv2.Laplacian(g, cv2.CV_64F).var() < 12:   # 纯色无效
            continue
        crops.append(crop)
print("crops:", len(crops))
idx = np.random.permutation(len(crops))[:8000]
arr = np.stack([crops[i] for i in idx], 0)
np.save(os.path.join(OUT, "imgs.npy"), arr)
print("saved", arr.shape, arr.dtype)
