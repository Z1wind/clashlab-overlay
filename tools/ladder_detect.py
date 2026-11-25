# -*- coding: utf-8 -*-
"""ladder_detect.py — 墙顶金帽/墙身块中心自动检测，输出中心距（纯离线）。

用法：
  python ladder_detect.py caps <L> [x0 y0 x1 y1]
  python ladder_detect.py wall <L> [x0 y0 x1 y1]
输出候选中心与最近邻间距；并导出标注裁片到 ladder_out/。
"""
import os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(ROOT, "out", "overlay", "ladder")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ladder_out")


def load(L):
    p = os.path.join(LADDER, f"zoom_L{L}.png")
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)


def components(mask, area_lo=15, area_hi=1500, min_dist=8):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    cents = []
    for i in range(1, n):
        a = stats[i, 4]
        if area_lo <= a <= area_hi:
            M = cv2.moments((lab == i).astype(np.uint8))
            if M["m00"] > 0:
                cents.append((M["m10"] / M["m00"], M["m01"] / M["m00"]))
    # 去重过近
    keep = []
    for c in cents:
        if all(np.hypot(c[0] - k[0], c[1] - k[1]) >= min_dist for k in keep):
            keep.append(c)
    return keep


def nn_spacings(cents):
    out = []
    for i, p in enumerate(cents):
        d = [np.hypot(p[0] - q[0], p[1] - q[1]) for j, q in enumerate(cents) if j != i]
        if d:
            out.append(min(d))
    return out


def cmd_caps(L, box=None):
    img = load(L)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # 金帽：黄/金 H 15-35, S>=120, V>=180
    mask = cv2.inRange(hsv, np.array([12, 120, 180]), np.array([35, 255, 255]))
    if box:
        x0, y0, x1, y1 = box
        m = np.zeros_like(mask)
        m[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
        mask = m
    cents = components(mask, 15, 1200, 10)
    sp = nn_spacings(cents)
    print(f"L{L} caps: n={len(cents)} nn spacings(px)={[round(s,1) for s in sp]}")
    if sp:
        sp = np.array(sp)
        print(f"  nn median={np.median(sp):.2f} mean={sp.mean():.2f} p25={np.percentile(sp,25):.2f} p75={np.percentile(sp,75):.2f}")
    ann = img.copy()
    for x, y in cents:
        cv2.circle(ann, (int(x), int(y)), 6, (0, 0, 255), 2)
    fp = os.path.join(OUT, f"L{L}_caps.png")
    cv2.imencode(".png", ann)[1].tofile(fp)
    print(fp)


def cmd_wall(L, box=None):
    img = load(L)
    b, g, r = img[:, :, 0].astype(int), img[:, :, 1].astype(int), img[:, :, 2].astype(int)
    # 奶油墙身：r,g 高，b 明显低，且非绿
    mask = ((r > 190) & (g > 175) & (b > 130) & (b < 220) & (r - b > 30)).astype(np.uint8) * 255
    if box:
        x0, y0, x1, y1 = box
        m = np.zeros_like(mask)
        m[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
        mask = m
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    cents = components(mask, 40, 3000, 14)
    sp = nn_spacings(cents)
    print(f"L{L} wall-body: n={len(cents)} nn spacings(px)={[round(s,1) for s in sp]}")
    if sp:
        sp = np.array(sp)
        print(f"  nn median={np.median(sp):.2f} mean={sp.mean():.2f}")
    ann = img.copy()
    for x, y in cents:
        cv2.circle(ann, (int(x), int(y)), 8, (0, 0, 255), 2)
    fp = os.path.join(OUT, f"L{L}_wall.png")
    cv2.imencode(".png", ann)[1].tofile(fp)
    print(fp)


if __name__ == "__main__":
    a = sys.argv[1:]
    box = list(map(int, a[3:7])) if len(a) >= 7 else None
    if a[0] == "caps":
        cmd_caps(a[1], box)
    else:
        cmd_wall(a[1], box)
