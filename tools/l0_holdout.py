# -*- coding: utf-8 -*-
"""l0_holdout.py — 38锚点留出验证 + 三块300x300裁片 + 基向量自洽量（纯离线）。
拟合沿用仿射晶格 p=O+i*a+j*b 手写爬山；A/B 按固定种子划分，互拟合互验收。
裁片从 v6_l0_grid_snapped.png 1:1 裁（网格已在图上）。"""
import cv2, numpy as np, os, math, random, json

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
EVID = os.path.join(ROOT, "out", "overlay", "v6_l0_grid_snapped.png")
OUTDIR = os.path.join(ROOT, "out", "overlay")

ANCHORS = [
    ("选择木屋", 235, 175), ("紫圣水罐T", 415, 175), ("黑紫建筑", 290, 250),
    ("金仓黄圆NW", 240, 285), ("紫圣水W", 195, 300), ("金堆NW", 355, 335),
    ("紫塔W", 165, 385), ("金仓黄圆W2", 105, 395), ("紫圣水W2", 105, 455),
    ("金仓黄圆NE", 505, 150), ("紫圣水NE", 610, 265), ("紫塔NE", 650, 270),
    ("黑罐NE", 710, 300), ("金堆NE", 670, 355), ("黑炮熔炉", 265, 290),
    ("黑塔N", 330, 285), ("黑塔C", 345, 405), ("中央暗黑大塔", 415, 455),
    ("金仓黄圆SW1", 185, 565), ("紫圣水SW", 215, 580), ("紫圣水E", 620, 275),
    ("黑罐E", 715, 300), ("橙熔炉E", 660, 320), ("深色储物E", 555, 365),
    ("黑塔E", 640, 375), ("大本营", 600, 490), ("紫圣水SE", 815, 545),
    ("黑罐SE", 705, 590), ("金仓黄圆SE", 610, 605), ("金仓黄圆SW2", 175, 555),
    ("橙熔炉SW", 275, 600), ("黑炮SW", 320, 665), ("金仓黄圆S", 400, 720),
    ("黑罐S", 595, 575), ("金仓黄圆S2", 550, 600), ("紫塔S", 595, 635),
    ("紫圣水S2", 510, 715), ("黑炮S2", 555, 715),
]
TILE_LO, TILE_HI = 21.0, 27.5


def snap_eval(params, pts):
    P = np.array([[x, y] for _, x, y in pts], dtype=float)
    ox, oy, ax, ay, bx, by = params
    M = np.column_stack([[ax, ay], [bx, by]])
    Minv = np.linalg.inv(M)
    ij = (P - [ox, oy]) @ Minv.T
    d = ij - np.round(ij)
    dd = np.sqrt((d ** 2).sum(axis=1))
    pen = 0.0
    for vv in (math.hypot(ax, ay), math.hypot(bx, by)):
        if vv < TILE_LO or vv > TILE_HI:
            pen += 200 * abs(vv - min(max(vv, TILE_LO), TILE_HI))
    return float((dd ** 2).sum()) + pen, dd, ij


def climb(x, pts, steps):
    def obj(p):
        return snap_eval(p, pts)[0]
    best = obj(x)
    for scale in steps:
        improved = True
        while improved:
            improved = False
            for i in range(len(x)):
                for d in (scale, -scale):
                    y = x.copy(); y[i] += d
                    v = obj(y)
                    if v < best - 1e-9:
                        x, best = y, v; improved = True
    return x, best


def fit(pts, seed_runs=500):
    rng = random.Random(seed_runs)
    best_x, best_v = None, np.inf
    for _ in range(seed_runs):
        th = rng.uniform(0, math.pi)
        m = rng.uniform(23.0, 25.0)
        a = m * np.array([math.cos(th), math.sin(th)])
        b = m * np.array([math.cos(th + math.pi / 2), math.sin(th + math.pi / 2)])
        s = np.array([rng.uniform(0, 905), rng.uniform(0, 1068), a[0], a[1], b[0], b[1]])
        x, v = climb(s, pts, [8.0, 3.0, 1.0, 0.3])
        if v < best_v:
            best_x, best_v = x, v
    return best_x


def report(tag, params, pts):
    _, dd, ij = snap_eval(params, pts)
    hit = int((dd <= 0.5).sum())
    hard = int((dd > 1.0).sum())
    print(f"--- {tag}: n={len(pts)} hit={hit}/{len(pts)} max={dd.max():.3f} mean={dd.mean():.3f} hard>1.0={hard}")
    for (nm, px, py), (i, j), dv in zip(pts, ij, dd):
        print(f"  {nm:10s} ({px},{py}) ij=({i:.2f},{j:.2f}) d={dv:.3f} {'OK' if dv<=0.5 else 'X'}")
    return hit, float(dd.max())


def main():
    # 固定种子划分：按索引奇偶（19/19）
    A = [ANCHORS[i] for i in range(0, 38, 2)]
    B = [ANCHORS[i] for i in range(1, 38, 2)]
    print(f"A={len(A)} B={len(B)}")

    # A 拟合 -> B 验收
    pA = fit(A)
    hB, mB = report("A fit -> B test", pA, B)
    # B 拟合 -> A 验收
    pB = fit(B)
    hA, mA = report("B fit -> A test", pB, A)

    # 基向量自洽量（全量解向量）
    full = np.array([473.2, 796.6, 13.17, 23.36, -20.06, 12.57])
    ax, ay, bx, by = full[2], full[3], full[4], full[5]
    la, lb = math.hypot(ax, ay), math.hypot(bx, by)
    cosang = (ax * bx + ay * by) / (la * lb)
    ang = math.degrees(math.acos(max(-1, min(1, cosang))))
    print(f"|a|={la:.3f} |b|={lb:.3f} |a|/|b|={la/lb:.3f} angle={ang:.2f}deg")
    print(f"tile_px 实测区间 23.8-24.4: |a|={'IN' if 23.8<=la<=24.4 else 'OUT'}, |b|={'IN' if 23.8<=lb<=24.4 else 'OUT'}")

    # 三块 300x300 1:1 裁片（网格已在证据图上）
    ev = cv2.imdecode(np.fromfile(EVID, np.uint8), cv2.IMREAD_COLOR)
    crops = [
        ("_1", 450, 340, "大本营区(600,490)"),
        ("_2", 205, 185, "金库金堆区(355,335)"),
        ("_3", 250, 570, "城墙拐角区(400,720)"),
    ]
    for tag, x0, y0, name in crops:
        c = ev[y0:y0+300, x0:x0+300].copy()
        cv2.putText(c, name, (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        fp = os.path.join(OUTDIR, f"v6_grid_zoom{tag}.png")
        cv2.imencode(".png", c)[1].tofile(fp)
        print("written", fp)

    # 汇总
    gen = (hB / len(B) >= 0.8 and mB <= 1.0) and (hA / len(A) >= 0.8 and mA <= 1.0)
    print(f"=== SUMMARY A->B {hB}/{len(B)} max{mB:.2f} | B->A {hA}/{len(A)} max{mA:.2f} | generalizes={gen}")


if __name__ == "__main__":
    main()
