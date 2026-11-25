# -*- coding: utf-8 -*-
"""l0_affine_fit.py — 诊断：仿射晶格吸附拟合（无scipy手写爬山）。
p = O + i*a + j*b；残差=锚点到最近整数格的距离；|a|,|b|≈tile_px(23.8-24.4)。
只读画布+锚点（内嵌），画 lattice 到 tools/base_out/affine_grid.png。"""
import cv2, numpy as np, os, math, random

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
OUT = os.path.join(ROOT, "tools", "base_out", "affine_grid.png")

ANCHORS = [
    (235, 175), (415, 175), (290, 250), (240, 285), (195, 300),
    (355, 335), (165, 385), (105, 395), (105, 455), (505, 150),
    (610, 265), (650, 270), (710, 300), (670, 355), (265, 290),
    (330, 285), (345, 405), (415, 455), (185, 565), (215, 580),
    (620, 275), (715, 300), (660, 320), (555, 365), (640, 375),
    (600, 490), (815, 545), (705, 590), (610, 605), (175, 555),
    (275, 600), (320, 665), (400, 720), (595, 575), (550, 600),
    (595, 635), (510, 715), (555, 715),
]
TILE_LO, TILE_HI = 21.0, 27.5


def resid(params, pts):
    ox, oy, ax, ay, bx, by = params
    O = np.array([ox, oy]); a = np.array([ax, ay]); b = np.array([bx, by])
    M = np.column_stack([a, b])
    Minv = np.linalg.inv(M)
    P = np.array(pts, dtype=float) - O
    ij = P @ Minv.T
    d = ij - np.round(ij)
    dd = np.sqrt((d ** 2).sum(axis=1))
    pen = 0.0
    for v in (np.linalg.norm(a), np.linalg.norm(b)):
        if v < TILE_LO or v > TILE_HI:
            pen += 200 * abs(v - min(max(v, TILE_LO), TILE_HI))
    return float((dd ** 2).sum()) + pen, dd, ij


def climb(x, obj, steps):
    best = obj(x)[0]
    for scale in steps:
        improved = True
        while improved:
            improved = False
            for i in range(len(x)):
                for d in (scale, -scale):
                    y = x.copy(); y[i] += d
                    v = obj(y)[0]
                    if v < best - 1e-9:
                        x, best = y, v; improved = True
    return x, best


def main():
    img = cv2.imdecode(np.fromfile(CANVAS, np.uint8), cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    rng = random.Random(11)
    best_x, best_v = None, np.inf
    starts = []
    # 初值：原点随机；两基向量正交、夹角随机（覆盖菱形对角轴），模长23-25
    for _ in range(600):
        th = rng.uniform(0, math.pi)
        m = rng.uniform(23.0, 25.0)
        a = m * np.array([math.cos(th), math.sin(th)])
        b = m * np.array([math.cos(th + math.pi / 2), math.sin(th + math.pi / 2)])
        s = np.array([rng.uniform(0, W), rng.uniform(0, H), a[0], a[1], b[0], b[1]])
        starts.append(s)
    def obj(p):
        return resid(p, ANCHORS)
    for s in starts:
        x, v = climb(s, obj, [8.0, 3.0, 1.0, 0.3])
        if v < best_v:
            best_x, best_v = x, v
    ox, oy, ax, ay, bx, by = best_x
    _, dd, ij = resid(best_x, ANCHORS)
    hit = int((dd <= 0.5).sum())
    print(f"O=({ox:.1f},{oy:.1f}) a=({ax:.2f},{ay:.2f}) |a|={math.hypot(ax,ay):.2f} b=({bx:.2f},{by:.2f}) |b|={math.hypot(bx,by):.2f}")
    print(f"sumresid={best_v:.3f} hit={hit}/{len(ANCHORS)} worst={dd.max():.3f}")
    for (px, py), (i, j), dv in zip(ANCHORS, ij, dd):
        print(f"({px},{py}) ij=({i:.2f},{j:.2f}) d={dv:.3f} {'OK' if dv<=0.5 else 'X'}")
    # 画 lattice
    vis = img.copy()
    O = np.array([ox, oy]); a = np.array([ax, ay]); b = np.array([bx, by])
    lo_i = math.floor(ij[:, 0].min()) - 2; hi_i = math.ceil(ij[:, 0].max()) + 2
    lo_j = math.floor(ij[:, 1].min()) - 2; hi_j = math.ceil(ij[:, 1].max()) + 2
    for ii in range(lo_i, hi_i + 1):
        p0 = O + ii * a + lo_j * b; p1 = O + ii * a + hi_j * b
        cv2.line(vis, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 200, 0), 1)
    for jj in range(lo_j, hi_j + 1):
        p0 = O + lo_i * a + jj * b; p1 = O + hi_i * a + jj * b
        cv2.line(vis, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 200, 0), 1)
    for (px, py), dv in zip(ANCHORS, dd):
        c = (0, 200, 0) if dv <= 0.5 else (0, 0, 220)
        cv2.circle(vis, (px, py), 6, c, -1)
    cv2.imencode(".png", vis)[1].tofile(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main()
