# -*- coding: utf-8 -*-
"""l0_wall_period.py — 直墙段凸块周期自相关（纯离线）。
给定两端点，取条带，奶油色墙掩码，投影到切线，自相关找 18-30px 主峰。"""
import cv2, numpy as np, os, math, sys

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
OUT = os.path.join(ROOT, "tools", "base_out", "wall_period.png")


def period(p0, p1, half=14, label=""):
    img = cv2.imdecode(np.fromfile(CANVAS, np.uint8), cv2.IMREAD_COLOR)
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    v = p1 - p0; L = np.linalg.norm(v); t = v / L; n = np.array([-t[1], t[0]])
    # 采样网格
    res = []
    for s in np.arange(0, L, 1.0):
        c = p0 + t * s
        acc = 0.0; cnt = 0
        for k in np.arange(-half, half + 1, 2.0):
            q = c + n * k
            xi, yi = int(round(q[0])), int(round(q[1]))
            if 0 <= xi < img.shape[1] and 0 <= yi < img.shape[0]:
                b, g, r = img[yi, xi]
                # 奶油墙：亮白/黄奶油，排除绿草(G占优)
                score = 1.0 if (r > 175 and g > 155 and b < 165 and r >= g - 15 and not (g > r and g > b)) else 0.0
                acc += score; cnt += 1
        res.append(acc / max(cnt, 1))
    sig = np.array(res)
    sig = sig - sig.mean()
    ac = np.correlate(sig, sig, "full")[len(sig) - 1:]
    # 找 18-30 主峰
    cand = []
    for lag in range(16, 34):
        if ac[lag] > ac[lag - 1] and ac[lag] > ac[lag + 1]:
            cand.append((ac[lag], lag))
    cand.sort(reverse=True)
    top = cand[:5]
    print(f"{label} L={L:.0f}px top lags={[(l, round(a,1)) for a,l in top]}")
    vis = img.copy()
    cv2.line(vis, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 0, 255), 2)
    cv2.imencode(".png", vis)[1].tofile(OUT)
    return top


if __name__ == "__main__":
    period((300, 662), (590, 712), half=16, label="bottom-wall")
    period((395, 250), (560, 205), half=16, label="top-wall")
    period((120, 430), (260, 590), half=16, label="left-wall")
    period((560, 150), (820, 300), half=16, label="outer-ne-wall")
