# -*- coding: utf-8 -*-
"""l0_final_scale.py — 尺度重标定稿（纯离线）。
说明：本画布内 1x1 直测不可得（金顶检测混入墙饰、墙段自相关平坦，见 l0_scale_measure*.py/l0_wall_period.py），
故尺度沿用 tile_px 链实测区间 23.8-24.4 中点 24.0，方向沿用吸附拟合基向量，两轴等长 24.0（ratio=1.000）。
状态 near（尺度继承链上测量，未在本帧独立复测）。
"""
import cv2, numpy as np, os, math, json, datetime

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
QUADJSON = os.path.join(ROOT, "config", "view_quads.json")
OUTIMG = os.path.join(ROOT, "out", "overlay", "v6_l0_grid_final.png")

# 吸附拟合方向（未重标）
A = np.array([13.17, 23.36]); B = np.array([-20.06, 12.57])
ua = A / np.linalg.norm(A); ub = B / np.linalg.norm(B)
TILE = 24.0  # tile_px 链 23.8-24.4 中点

# O 沿用全量吸附拟合原点（l0_snap_final 38/38 解）
O_FIT = np.array([473.2, 796.6])


def main():
    img = cv2.imdecode(np.fromfile(CANVAS, np.uint8), cv2.IMREAD_COLOR)
    Hc, Wc = img.shape[:2]
    a = TILE * ua; b = TILE * ub
    O = O_FIT.copy()

    # 44x44 平台四顶点（tile(0,0)=(T)）
    T = O
    R = O + 44 * a
    B = O + 44 * a + 44 * b
    L = O + 44 * b
    def inside(p): return 0 <= p[0] <= Wc and 0 <= p[1] <= Hc
    verts = {"T": T, "R": R, "B": B, "L": L}
    all_in = all(inside(v) for v in verts.values())
    print("O=", O, "a=", a, "b=", b)
    for k, v in verts.items():
        print(f"{k}=({v[0]:.1f},{v[1]:.1f}) inside={inside(v)}")

    # 网格图：在画布内画晶格线，标出出画范围
    vis = img.copy()
    # 找画布内可见的 i,j 范围
    # 反解：对画布四角求 i,j
    corners = np.array([[0, 0], [Wc, 0], [Wc, Hc], [0, Hc]], float)
    Minv = np.linalg.inv(np.column_stack([a, b]))
    ij_c = (corners - O) @ Minv.T
    lo_i = math.floor(ij_c[:, 0].min()) - 1; hi_i = math.ceil(ij_c[:, 0].max()) + 1
    lo_j = math.floor(ij_c[:, 1].min()) - 1; hi_j = math.ceil(ij_c[:, 1].max()) + 1
    for ii in range(lo_i, hi_i + 1):
        p0 = O + ii * a + lo_j * b; p1 = O + ii * a + hi_j * b
        cv2.line(vis, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 200, 0), 1)
    for jj in range(lo_j, hi_j + 1):
        p0 = O + lo_i * a + jj * b; p1 = O + hi_i * a + jj * b
        cv2.line(vis, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 200, 0), 1)
    # 顶点标记（出画的画在最近边缘并标红）
    for k, v in verts.items():
        c = (0, 200, 0) if inside(v) else (0, 0, 255)
        cl = np.clip(v, [0, 0], [Wc - 1, Hc - 1])
        cv2.circle(vis, tuple(cl.astype(int)), 10, c, -1)
        cv2.putText(vis, k, tuple(cl.astype(int) + [12, -6]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, c, 2)
    cv2.putText(vis, f"tile={TILE} |a|=|b|=24.0 ratio=1.000 | verts_in={all_in}",
                (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    cv2.imencode(".png", vis)[1].tofile(OUTIMG)

    qj = json.load(open(QUADJSON, encoding="utf-8"))
    if "L0_snapped" in qj:
        qj["L0_snapped"]["status"] = "scale_unverified"
    qj["status"] = "FAIL"
    qj["L0_snapped_v2"] = {
        "lattice": {
            "O": [round(float(O[0]), 3), round(float(O[1]), 3)],
            "a": [round(float(a[0]), 3), round(float(a[1]), 3)],
            "b": [round(float(b[0]), 3), round(float(b[1]), 3)],
        },
        "norm_a": TILE, "norm_b": TILE, "ratio": 1.0,
        "quad_44": {k: [round(float(v[0]), 3), round(float(v[1]), 3)] for k, v in verts.items()},
        "verts_in_canvas": bool(all_in),
        "tile_px": TILE,
        "canvas": [Wc, Hc],
        "holdout": "16/19 & 18/19",
        "status": "near",
        "scale_note": "本帧1x1直测不可得(金顶检测混墙饰/墙自相关平坦)；尺度继承tile_px链23.8-24.4中点24.0，方向用吸附拟合，两轴等长",
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    json.dump(qj, open(QUADJSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("written", OUTIMG, QUADJSON)


if __name__ == "__main__":
    main()
