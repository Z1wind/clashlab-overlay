# -*- coding: utf-8 -*-
"""ladder_period.py — 草地窗内 2D-FFT 径向周期 + 自相关环半径（纯离线）。

用法：python ladder_period.py <L> <lo_px> <hi_px> [x0 y0 x1 y1]
输出 FFT 径向主峰周期、自相关第一环半径；窗默认全帧。
"""
import os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(ROOT, "out", "overlay", "ladder")


def load(L):
    p = os.path.join(LADDER, f"zoom_L{L}.png")
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)


def radial_profile(F):
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


def fft_period(win, lo, hi):
    h, w = win.shape
    wm = np.outer(np.hanning(h), np.hanning(w))
    F = np.fft.fftshift(np.abs(np.fft.fft2(win * wm)))
    cy, cx = h // 2, w // 2
    F[cy - 4:cy + 5, cx - 4:cx + 5] = 0
    prof = radial_profile(F)
    b_lo = max(3, int(w / hi))
    b_hi = min(len(prof) - 1, int(w / lo))
    seg = prof[b_lo:b_hi + 1]
    i = int(np.argmax(seg))
    return float(w / (b_lo + i)), b_lo + i, float(seg[i])


def autocorr_ring(win, lo, hi):
    w = win - win.mean()
    F = np.fft.fft2(w * np.outer(np.hanning(w.shape[0]), np.hanning(w.shape[1])))
    ac = np.fft.fftshift(np.abs(np.fft.ifft2(F * np.conj(F))))
    prof = radial_profile(ac)
    b_lo = max(3, int(win.shape[1] / hi))
    b_hi = min(len(prof) - 1, int(win.shape[1] / lo))
    seg = prof[b_lo:b_hi + 1]
    i = int(np.argmax(seg))
    return float(b_lo + i), float(seg[i])


if __name__ == "__main__":
    L = sys.argv[1]
    lo, hi = float(sys.argv[2]), float(sys.argv[3])
    box = list(map(int, sys.argv[4:8])) if len(sys.argv) >= 8 else None
    img = load(L)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float64)
    if box:
        x0, y0, x1, y1 = box
        g = g[y0:y1, x0:x1]
    p, bin_k, mag = fft_period(g, lo, hi)
    ring, ringmag = autocorr_ring(g, lo, hi)
    print(f"L{L} box={box} FFT周期={p:.2f}px (bin={bin_k}, mag={mag:.0f})  "
          f"自相关环={ring:.1f}px (mag={ringmag:.0f})")
