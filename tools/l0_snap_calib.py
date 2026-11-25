# -*- coding: utf-8 -*-
"""l0_snap_calib.py — L0 画布晶格吸附自标定（纯离线，无scipy，手写坐标下降+随机重启）。

目标：优化 quad(T/R/B/L 8自由度, H/W∈[0.4,0.6])，使人工锚点经 homography 映射后
尽可能落整数格；残差=到最近整数格欧氏距离。验收: ≥8/10 ≤0.5格, 无 >1.0格。
只读 v6_l0_three_shot_base.png + config/view_quads.json 初值；写
out/overlay/v6_l0_grid_snapped.png，并向 config 追加 L0_snapped（不覆盖旧键）。
"""
import cv2, numpy as np, os, json, math, random, datetime

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
QUADJSON = os.path.join(ROOT, "config", "view_quads.json")
OUTIMG = os.path.join(ROOT, "out", "overlay", "v6_l0_grid_snapped.png")

# --- 人工锚点（画布像素坐标，2x网格裁片读数，±8px）---
ANCHORS = [
    ("选择木屋", 235, 175),
    ("紫圣水罐T", 415, 175),
    ("黑紫建筑", 290, 250),
    ("金仓黄圆NW", 240, 285),
    ("紫圣水W", 195, 300),
    ("金堆NW", 355, 335),
    ("紫塔W", 165, 385),
    ("金仓黄圆W2", 105, 395),
    ("紫圣水W2", 105, 455),
    ("金仓黄圆NE", 505, 150),
    ("紫圣水NE", 610, 265),
    ("紫塔NE", 650, 270),
    ("黑罐NE", 710, 300),
    ("金堆NE", 670, 355),
    ("黑炮熔炉", 265, 290),
    ("黑塔N", 330, 285),
    ("黑塔C", 345, 405),
    ("中央暗黑大塔", 415, 455),
    ("金仓黄圆SW1", 185, 565),
    ("紫圣水SW", 215, 580),
    ("紫圣水E", 620, 275),
    ("黑罐E", 715, 300),
    ("橙熔炉E", 660, 320),
    ("深色储物E", 555, 365),
    ("黑塔E", 640, 375),
    ("大本营", 600, 490),
    ("紫圣水SE", 815, 545),
    ("黑罐SE", 705, 590),
    ("金仓黄圆SE", 610, 605),
    ("金仓黄圆SW2", 175, 555),
    ("橙熔炉SW", 275, 600),
    ("黑炮SW", 320, 665),
    ("金仓黄圆S", 400, 720),
    ("黑罐S", 595, 575),
    ("金仓黄圆S2", 550, 600),
    ("紫塔S", 595, 635),
    ("紫圣水S2", 510, 715),
    ("黑炮S2", 555, 715),
]

RATIO_LO, RATIO_HI = 0.40, 0.60
ACCEPT, HARD = 0.5, 1.0


def snap_resid_uv(uv):
    """uv: (n,2) tile 坐标；返回每点到最近整数格的欧氏距离。"""
    d = np.abs(uv - np.round(uv))
    return np.sqrt((d ** 2).sum(axis=1))


def quad_homography(T, R, B, L, M):
    """四角 -> 目标矩形 (0,0)-(M,0)-(M,M*0.5)-(0,M*0.5) 的透视矩阵。"""
    src = np.float32([T, R, B, L])
    dst = np.float32([[0, 0], [M, 0], [M, M * 0.5], [0, M * 0.5]])
    return cv2.getPerspectiveTransform(src, dst)


def quad_convex(T, R, B, L):
    pts = [T, R, B, L]
    signs = []
    for i in range(4):
        p0, p1, p2 = pts[i], pts[(i + 1) % 4], pts[(i + 2) % 4]
        cr = (p1[0] - p0[0]) * (p2[1] - p1[1]) - (p1[1] - p0[1]) * (p2[0] - p1[0])
        signs.append(np.sign(cr))
    return all(s == signs[0] and s != 0 for s in signs)


def _edge_ratio(T, R, B, L):
    # 屏幕投影 H/W = |TB|/|LR|（菱形竖/横）
    h = math.hypot(T[0] - B[0], T[1] - B[1])
    w = math.hypot(L[0] - R[0], L[1] - R[1])
    return h / w if w > 1e-6 else 9.9


M_FIX = 40.0  # 平台横向格数（canvas_tiles≈39.6，固定避免尺度塌缩）


def quad_area(T, R, B, L):
    # 鞋带公式
    pts = [T, R, B, L]
    a = 0.0
    for i in range(4):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % 4]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def homog_resid(params, anchors, W, H, return_detail=False):
    T = params[0:2]; R = params[2:4]; B = params[4:6]; L = params[6:8]
    pen = 0.0
    # 画布内
    for p in (T, R, B, L):
        if p[0] < 0 or p[0] > W or p[1] < 0 or p[1] > H:
            pen += 100 * (abs(p[0]) + abs(p[1]) + W + H)
    # 凸
    if not quad_convex(T, R, B, L):
        pen += 50.0
    # 屏幕 H/W 约束
    hw = _edge_ratio(T, R, B, L)
    if hw < RATIO_LO or hw > RATIO_HI:
        pen += 80.0 * abs(hw - min(max(hw, RATIO_LO), RATIO_HI))
    # 防塌缩：quad 面积 ≥ 0.28 画布面积
    area = quad_area(T, R, B, L)
    if area < 0.28 * W * H:
        pen += 200.0 * (0.28 * W * H - area) / (W * H)
    Hm = quad_homography(T, R, B, L, M_FIX)
    pa = np.float32([[a[1], a[2]] for a in anchors]).reshape(-1, 1, 2)
    uv = cv2.perspectiveTransform(pa, Hm).reshape(-1, 2)
    d = snap_resid_uv(uv)
    # 防塌缩：锚点 uv 跨度须铺满平台（u≥0.7M, v≥0.35M）
    us, vs = uv[:, 0], uv[:, 1]
    span_u = us.max() - us.min(); span_v = vs.max() - vs.min()
    if span_u < 0.7 * M_FIX:
        pen += 100.0 * (0.7 * M_FIX - span_u) / M_FIX
    if span_v < 0.35 * M_FIX:
        pen += 100.0 * (0.35 * M_FIX - span_v) / M_FIX
    s = float((d ** 2).sum()) + pen
    if return_detail:
        return s, uv, d
    return s


def hill_climb(params, obj, steps, iters=60):
    """手写坐标下降：每维双向步长搜索，步长逐次减半。"""
    x = np.array(params, dtype=float)
    best = obj(x)
    for scale in steps:
        improved = True
        while improved:
            improved = False
            for i in range(len(x)):
                for delta in (scale, -scale):
                    y = x.copy(); y[i] += delta
                    v = obj(y)
                    if v < best - 1e-9:
                        x, best = y, v; improved = True
    return x, best


def main():
    img = cv2.imdecode(np.fromfile(CANVAS, np.uint8), cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    anchors = [(n, float(x), float(y)) for n, x, y in ANCHORS]

    qj = json.load(open(QUADJSON, encoding="utf-8"))
    q0 = qj["quad"]
    seed = [q0["T"][0], q0["T"][1], q0["R"][0], q0["R"][1],
            q0["B"][0], q0["B"][1], q0["L"][0], q0["L"][1]]

    rng = random.Random(7)
    def obj(p):
        return homog_resid(p, anchors, W, H)

    best_x, best_v = None, np.inf
    # 初值 + 随机重启
    starts = [seed]
    for _ in range(150):
        s = seed.copy()
        s[0] += rng.uniform(-160, 160); s[1] += rng.uniform(-160, 160)
        s[2] += rng.uniform(-160, 160); s[3] += rng.uniform(-160, 160)
        s[4] += rng.uniform(-160, 160); s[5] += rng.uniform(-160, 160)
        s[6] += rng.uniform(-160, 160); s[7] += rng.uniform(-160, 160)
        starts.append(s)
    for s in starts:
        x, v = hill_climb(s, obj, [40.0, 15.0, 6.0, 2.0, 0.6, 0.2])
        if v < best_v:
            best_x, best_v = x, v

    params = best_x
    T, R, B, L = params[0:2], params[2:4], params[4:6], params[6:8]
    M = M_FIX
    resid, uv, d = homog_resid(params, anchors, W, H, return_detail=True)
    HW = _edge_ratio(T, R, B, L)

    rows = []
    n_hit = 0
    worst = 0.0
    for (name, ax, ay), (u, v), dd in zip(anchors, uv, d):
        ok = dd <= ACCEPT
        n_hit += ok
        worst = max(worst, dd)
        rows.append((name, ax, ay, round(u, 3), round(v, 3), round(float(dd), 3), ok))

    print("=== homography snap ===")
    print(f"T={T} R={R} B={B} L={L} M={M:.2f} H/W(edge)={HW:.3f} sumresid={resid:.3f}")
    print(f"quad_area={quad_area(T,R,B,L):.0f} canvas_area={W*H:.0f}")
    for nm, ax, ay, u, v, dd, ok in rows:
        print(f"{nm:10s} ({ax:.0f},{ay:.0f}) tile=({u:.2f},{v:.2f}) d={dd:.3f} {'OK' if ok else 'X'}")
    print(f"hit {n_hit}/{len(anchors)} worst={worst:.3f}")

    # --- 证据图：画拟合网格 + 锚点 ---
    vis = img.copy()
    Hm = quad_homography(T, R, B, L, M)
    inv = np.linalg.inv(Hm)
    # 画 uv 格线（覆盖锚点范围向外扩2格）
    us = [row[3] for row in rows]; vs = [row[4] for row in rows]
    u0, u1 = math.floor(min(us)) - 2, math.ceil(max(us)) + 2
    v0, v1 = math.floor(min(vs)) - 2, math.ceil(max(vs)) + 2
    for ui in range(u0, u1 + 1):
        p0 = inv @ np.array([ui, v0, 1.0]); p0 /= p0[2]
        p1 = inv @ np.array([ui, v1, 1.0]); p1 /= p1[2]
        cv2.line(vis, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (0, 200, 0), 1)
    for vi in range(v0, v1 + 1):
        p0 = inv @ np.array([u0, vi, 1.0]); p0 /= p0[2]
        p1 = inv @ np.array([u1, vi, 1.0]); p1 /= p1[2]
        cv2.line(vis, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (0, 200, 0), 1)
    # 四角
    for p, c in ((T, (0, 0, 255)), (R, (255, 0, 0)), (B, (0, 165, 255)), (L, (255, 0, 255))):
        cv2.circle(vis, (int(p[0]), int(p[1])), 8, c, -1)
    for nm, ax, ay, u, v, dd, ok in rows:
        c = (0, 200, 0) if ok else (0, 0, 220)
        cv2.circle(vis, (int(ax), int(ay)), 6, c, -1)
        cv2.putText(vis, f"{dd:.2f}", (int(ax) + 8, int(ay) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 1)
    cv2.imencode(".png", vis)[1].tofile(OUTIMG)

    # --- 写 config：追加 L0_snapped，旧键标 FAIL ---
    qj["status"] = "FAIL"
    qj["L0_snapped"] = {
        "quad": {
            "T": [round(float(T[0]), 3), round(float(T[1]), 3)],
            "R": [round(float(R[0]), 3), round(float(R[1]), 3)],
            "B": [round(float(B[0]), 3), round(float(B[1]), 3)],
            "L": [round(float(L[0]), 3), round(float(L[1]), 3)],
        },
        "H_W": round(float(HW), 4),
        "M_tiles": round(float(M), 3),
        "fit_resid": round(float(resid), 4),
        "quad_area": round(float(quad_area(T, R, B, L)), 1),
        "anchors_n": len(anchors),
        "anchors_pass": int(n_hit),
        "worst_dev": round(float(worst), 4),
        "tile_px": 24.0,
        "canvas": [W, H],
        "method": "homography lattice snap, hand hill-climb, no scipy",
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    json.dump(qj, open(QUADJSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("written", OUTIMG, QUADJSON)


if __name__ == "__main__":
    main()
