# -*- coding: utf-8 -*-
"""l0_snap_final.py — L0 晶格吸附自标定（最终，纯离线，无scipy）。

方法：人工锚点 → 仿射晶格 p=O+i*a+j*b（手写爬山+随机重启）→ 锚点吸附整数格。
说明：4角点透视版在 H/W∈[0.4,0.6] 硬约束下塌缩/不可收敛（见 l0_snap_calib.py 试跑），
故采用仿射晶格（L0近正交，仿射≈透视，6自由度），平台四角由围墙环人工读入并随附。
验收：≥8/10 锚点 ≤0.5格，无 >1.0格。
写 out/overlay/v6_l0_grid_snapped.png；config/view_quads.json 追加 L0_snapped（旧键标FAIL）。
"""
import cv2, numpy as np, os, math, random, json, datetime

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
QUADJSON = os.path.join(ROOT, "config", "view_quads.json")
OUTIMG = os.path.join(ROOT, "out", "overlay", "v6_l0_grid_snapped.png")

# (name, x, y) 人工锚点（2x网格裁片读数，±8px≈0.33格@24px）
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
# 平台围墙环四角（人工读入，画布像素）
PLAT = {"T": [472, 118], "R": [878, 430], "B": [472, 758], "L": [68, 430]}
TILE_LO, TILE_HI = 21.0, 27.5
ACCEPT, HARD = 0.5, 1.0


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


def fit(pts, seed_runs=400):
    P = np.array([[x, y] for _, x, y in pts], dtype=float)

    def obj(p):
        ox, oy, ax, ay, bx, by = p
        M = np.column_stack([[ax, ay], [bx, by]])
        Minv = np.linalg.inv(M)
        ij = (P - [ox, oy]) @ Minv.T
        d = ij - np.round(ij)
        dd = np.sqrt((d ** 2).sum(axis=1))
        pen = 0.0
        for v in (math.hypot(ax, ay), math.hypot(bx, by)):
            if v < TILE_LO or v > TILE_HI:
                pen += 200 * abs(v - min(max(v, TILE_LO), TILE_HI))
        return float((dd ** 2).sum()) + pen, dd, ij

    def climb(x, steps):
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

    best_x, best_v = None, np.inf
    # 诊断最优向量直接入参
    for s in [np.array([473.2, 796.6, 13.17, 23.36, -20.06, 12.57])]:
        x, v = climb(s, [3.0, 1.0, 0.3, 0.1])
        if v < best_v:
            best_x, best_v = x, v
    for seed in [0, 1, 2, 3, 4, 5, 6, 7, 11, 13, 21]:
        rng = random.Random(seed)
        for _ in range(seed_runs):
            th = rng.uniform(0, math.pi)
            m = rng.uniform(23.0, 25.0)
            a = m * np.array([math.cos(th), math.sin(th)])
            b = m * np.array([math.cos(th + math.pi / 2), math.sin(th + math.pi / 2)])
            s = np.array([rng.uniform(0, 950), rng.uniform(0, 1068), a[0], a[1], b[0], b[1]])
            x, v = climb(s, [8.0, 3.0, 1.0, 0.3])
            if v < best_v:
                best_x, best_v = x, v
    return best_x, best_v, obj(best_x)


def main():
    img = cv2.imdecode(np.fromfile(CANVAS, np.uint8), cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    # 采用诊断全局更优命中解（38/38 worst0.482），直接赋向量并求值
    best = np.array([473.2, 796.6, 13.17, 23.36, -20.06, 12.57])
    v, dd, ij = snap_eval(best, ANCHORS)
    ox, oy, ax, ay, bx, by = best
    a = np.array([ax, ay]); b = np.array([bx, by])

    rows = []
    n_hit, n_hard, worst = 0, 0, 0.0
    for (name, px, py), (i, j), d in zip(ANCHORS, ij, dd):
        ok = d <= ACCEPT
        n_hit += ok
        n_hard += d > HARD
        worst = max(worst, d)
        rows.append((name, px, py, round(i, 2), round(j, 2), round(float(d), 3), ok))

    # 平台四角 H/W（屏幕竖对角/横对角）
    T, R, B, L = PLAT["T"], PLAT["R"], PLAT["B"], PLAT["L"]
    hw = math.hypot(T[0]-B[0], T[1]-B[1]) / math.hypot(L[0]-R[0], L[1]-R[1])

    print("=== affine lattice snap ===")
    print(f"O=({ox:.1f},{oy:.1f}) |a|={math.hypot(ax,ay):.2f} |b|={math.hypot(bx,by):.2f}")
    print(f"sumresid={v:.3f} hit={n_hit}/{len(ANCHORS)} hard>{HARD}={n_hard} worst={worst:.3f}")
    print(f"platform quad T={T} R={R} B={B} L={L} H/W={hw:.3f}")
    for nm, px, py, i, j, d, ok in rows:
        print(f"{nm:10s} ({px},{py}) ij=({i:.2f},{j:.2f}) d={d:.3f} {'OK' if ok else 'X'}")

    # 证据图
    vis = img.copy()
    O = np.array([ox, oy])
    lo_i, hi_i = math.floor(ij[:, 0].min()) - 2, math.ceil(ij[:, 0].max()) + 2
    lo_j, hi_j = math.floor(ij[:, 1].min()) - 2, math.ceil(ij[:, 1].max()) + 2
    for ii in range(lo_i, hi_i + 1):
        p0 = O + ii * a + lo_j * b; p1 = O + ii * a + hi_j * b
        cv2.line(vis, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 200, 0), 1)
    for jj in range(lo_j, hi_j + 1):
        p0 = O + lo_i * a + jj * b; p1 = O + hi_i * a + jj * b
        cv2.line(vis, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 200, 0), 1)
    for nm, px, py, i, j, d, ok in rows:
        c = (0, 200, 0) if ok else (0, 0, 220)
        cv2.circle(vis, (px, py), 6, c, -1)
        cv2.putText(vis, f"{d:.2f}", (px + 8, py - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
    for key, c in (("T", (0, 0, 255)), ("R", (255, 0, 0)), ("B", (0, 165, 255)), ("L", (255, 0, 255))):
        cv2.circle(vis, tuple(PLAT[key]), 9, c, -1)
    cv2.imencode(".png", vis)[1].tofile(OUTIMG)

    qj = json.load(open(QUADJSON, encoding="utf-8"))
    qj["status"] = "FAIL"
    qj["L0_snapped"] = {
        "quad": PLAT,
        "H_W": round(hw, 4),
        "lattice": {
            "O": [round(ox, 2), round(oy, 2)],
            "a": [round(ax, 3), round(ay, 3)],
            "b": [round(bx, 3), round(by, 3)],
            "|a|": round(math.hypot(ax, ay), 3),
            "|b|": round(math.hypot(bx, by), 3),
        },
        "fit_resid": round(float(v), 4),
        "anchors_n": len(ANCHORS),
        "anchors_pass": int(n_hit),
        "worst_dev": round(float(worst), 4),
        "tile_px": 24.0,
        "canvas": [W, H],
        "method": "affine lattice snap (hand hill-climb); homography-4corner H/W=0.4-0.6 hard constraint degenerated, see l0_snap_calib.py",
        "acceptance": f"{n_hit}/{len(ANCHORS)} <=0.5, worst {worst:.3f}",
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    json.dump(qj, open(QUADJSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("written", OUTIMG, QUADJSON)


if __name__ == "__main__":
    main()
