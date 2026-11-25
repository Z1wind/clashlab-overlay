# -*- coding: utf-8 -*-
"""l0_scale_measure.py — 用黄色1x1小柱(金顶)沿 a/b 轴量 1 格像素间距（纯离线）。
检测金顶小 blob，配对近邻，投影到拟合轴方向，取中位间距；出检测叠加图供核验。"""
import cv2, numpy as np, os, math

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
OUT = os.path.join(ROOT, "tools", "base_out", "scale_detect.png")

# 拟合轴方向（归一化）
A = np.array([13.17, 23.36]); B = np.array([-20.06, 12.57])
ua = A / np.linalg.norm(A); ub = B / np.linalg.norm(B)


def main():
    img = cv2.imdecode(np.fromfile(CANVAS, np.uint8), cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    mask = ((r > 170) & (g > 140) & (b < 110)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(mask)
    pts = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if 15 <= area <= 250:
            cx, cy = cent[i]
            pts.append((cx, cy, area))
    print(f"blobs={len(pts)}")
    vis = img.copy()
    for cx, cy, area in pts:
        cv2.circle(vis, (int(cx), int(cy)), 5, (0, 0, 255), 1)

    # 近邻配对，投影到两轴
    pa, pb = [], []
    P = np.array([[p[0], p[1]] for p in pts])
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = P[j] - P[i]
            dist = np.linalg.norm(d)
            if 16 < dist < 34:
                ta = abs(d @ ua); tb = abs(d @ ub)
                # 沿 a 轴：b 投影小
                if tb < 6 and ta > 16:
                    pa.append(ta)
                if ta < 6 and tb > 16:
                    pb.append(tb)
    pa, pb = np.array(pa), np.array(pb)
    print(f"pairs along a: {len(pa)} median={np.median(pa) if len(pa) else float('nan'):.3f} mean={pa.mean() if len(pa) else float('nan'):.3f}")
    print(f"pairs along b: {len(pb)} median={np.median(pb) if len(pb) else float('nan'):.3f} mean={pb.mean() if len(pb) else float('nan'):.3f}")
    if len(pa): print("a samples:", np.round(np.sort(pa), 1))
    if len(pb): print("b samples:", np.round(np.sort(pb), 1))
    cv2.imencode(".png", vis)[1].tofile(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main()
