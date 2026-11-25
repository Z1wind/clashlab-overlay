# -*- coding: utf-8 -*-
"""ladder_period2.py — 草皮窗 FFT 多峰 + 自相关局域峰（纯离线）。

用法：python ladder_period2.py <L> <lo> <hi> <x0> <y0> <x1> <y1>
打印 FFT 径向 top 峰（周期=窗宽/bin）与自相关径向局域峰。
"""
import os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(ROOT, "out", "overlay", "ladder")


def load(L):
    p = os.path.join(LADDER, f"zoom_L{L}.png")
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)


def radial(F):
    h, w = F.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(yy - cy, xx - cx)
    rb = np.round(r).astype(int)
    maxr = min(h, w) // 2 - 2
    prof = np.zeros(maxr)
    cnt = np.zeros(maxr)
    np.add.at(prof, rb[rb < maxr], F[rb < maxr])
    np.add.at(cnt, rb[rb < maxr], 1)
    return np.divide(prof, cnt, out=np.zeros_like(prof), where=cnt > 0)


if __name__ == "__main__":
    L = sys.argv[1]
    lo, hi = float(sys.argv[2]), float(sys.argv[3])
    x0, y0, x1, y1 = map(int, sys.argv[4:8])
    img = load(L)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float64)
    win = g[y0:y1, x0:x1]
    h, w = win.shape
    wm = np.outer(np.hanning(h), np.hanning(w))
    F = np.fft.fftshift(np.abs(np.fft.fft2(win * wm)))
    cy, cx = h // 2, w // 2
    F[cy - 4:cy + 5, cx - 4:cx + 5] = 0
    prof = radial(F)
    b_lo = max(3, int(w / hi))
    b_hi = min(len(prof) - 1, int(w / lo))
    seg = prof[b_lo:b_hi + 1]
    order = np.argsort(seg)[::-1][:6]
    print(f"L{L} window=({x0},{y0})-({x1},{y1}) {w}x{h}")
    for i in order:
        bin_k = b_lo + i
        print(f"  FFT bin={bin_k} period={w/bin_k:.1f}px mag={seg[i]:.0f}")
    # 自相关径向局域峰
    F2 = np.fft.fft2(win - win.mean())
    ac = np.fft.fftshift(np.abs(np.fft.ifft2(F2 * np.conj(F2))))
    rp = radial(ac)
    rp[: int(w / hi)] = 0
    rp[int(w / lo):] = 0
    # 局域极大
    peaks = []
    for r in range(3, len(rp) - 3):
        if rp[r] > rp[r - 1] and rp[r] > rp[r + 1] and rp[r] > 0.1 * rp.max():
            peaks.append((r, rp[r]))
    peaks.sort(key=lambda t: -t[1])
    for r, m in peaks[:6]:
        print(f"  AC ring r={r}px mag={m:.0f}")
