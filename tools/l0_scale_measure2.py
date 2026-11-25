# -*- coding: utf-8 -*-
"""l0_scale_measure2.py — 中央草坪孤立金顶小柱检测 + 沿轴配对量距（纯离线）。"""
import cv2, numpy as np, os, math

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
OUT = os.path.join(ROOT, "tools", "base_out", "scale_detect2.png")
A = np.array([13.17, 23.36]); B = np.array([-20.06, 12.57])
ua = A / np.linalg.norm(A); ub = B / np.linalg.norm(B)


def main():
    img = cv2.imdecode(np.fromfile(CANVAS, np.uint8), cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    # 金顶：亮黄，避开金堆/金仓大色块
    mask = ((r > 190) & (g > 160) & (b < 90)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(mask)
    pts = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        x, y, w, h = stats[i, :4]
        if 25 <= area <= 160 and w <= 26 and h <= 26:
            cx, cy = cent[i]
            # 只保留中央草坪带（避开边缘森林/水/金仓）
            if 330 < cx < 730 and 280 < cy < 580:
                pts.append((cx, cy))
    print(f"pts={len(pts)}")
    vis = img.copy()
    for cx, cy in pts:
        cv2.circle(vis, (int(cx), int(cy)), 6, (0, 0, 255), 2)
        cv2.putText(vis, f"({int(cx)},{int(cy)})", (int(cx)+8, int(cy)-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    P = np.array(pts)
    pa, pb = [], []
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = P[j] - P[i]
            dist = np.linalg.norm(d)
            if 16 < dist < 34:
                ta = abs(float(d @ ua)); tb = abs(float(d @ ub))
                if tb < 5 and ta > 16: pa.append(ta)
                if ta < 5 and tb > 16: pb.append(tb)
    pa, pb = np.array(pa), np.array(pb)
    print("along a n=%d median=%.2f mean=%.2f" % (len(pa), np.median(pa) if len(pa) else -1, pa.mean() if len(pa) else -1))
    print("along b n=%d median=%.2f mean=%.2f" % (len(pb), np.median(pb) if len(pb) else -1, pb.mean() if len(pb) else -1))
    if len(pa): print("a:", np.round(np.sort(pa), 1))
    if len(pb): print("b:", np.round(np.sort(pb), 1))
    cv2.imencode(".png", vis[260:600, 310:750],)[1].tofile(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main()
