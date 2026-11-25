# -*- coding: utf-8 -*-
"""VL-CV 离线分析（只读调用 clashlab，不改任何 .py / info.json）。

两件事：
1) grass_contour 在固定视角假设下的尺度敏感性：剥 chrome 后按
   0.6/0.8/1.0/1.25/1.5 重采样，调 calib.detect_village_quad，
   记录检出/方法/置信/四顶点残差(px, 格)。s=1.0 为真实截图，其余为重采样模拟。
2) 宽高比归因：手点 quad 对称不变量 + 重采样序列中 bbox W/H 是否随缩放改变。

本脚本只打印，不落盘。
"""
import os, sys, json
import numpy as np
import cv2

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, ROOT)
from clashlab.calib import detect_village_quad  # noqa: E402
from clashlab.geo import order_diamond          # noqa: E402

BASE = os.path.join(ROOT, "bases", "th16", "war_20261123")

# 手工 quad（图片像素，T,R,B,L），与 tools/build_prebattle.py 同值（只读引用）
QUADS = {
    "14_kekejdj": [[520, 110], [905, 345], [512, 555], [150, 350]],
    "15_qembzi":  [[512, 110], [915, 355], [512, 575], [95, 365]],
    "16_diddieyang": [[508, 105], [925, 365], [508, 560], [95, 360]],
    "17_akib":    [[500, 105], [930, 360], [500, 565], [90, 360]],
}
SCALES = [0.6, 0.8, 1.0, 1.25, 1.5]

with open(os.path.join(BASE, "_verify", "frame_bounds.json"), encoding="utf-8") as f:
    BOUNDS = json.load(f)["images"]


def bbox_wh(q):
    xs, ys = q[:, 0], q[:, 1]
    return float(xs.max() - xs.min()), float(ys.max() - ys.min())


def invariants(q):
    """q: T,R,B,L。返回 bbox W/H、对角比 d_h/d_v、对称偏移。"""
    T, R, B, L = q
    W, H = bbox_wh(q)
    dx = np.linalg.norm(R - L)
    dy = np.linalg.norm(B - T)
    mx = (L[0] + R[0]) / 2.0
    my = (L[1] + R[1]) / 2.0
    return {
        "W": W, "H": H, "ratio_wh": W / H,
        "diag_ratio": dx / dy,
        "Tx-mx": T[0] - mx, "Bx-mx": B[0] - mx,
        "midTy-my": (T[1] + B[1]) / 2.0 - my,
    }


print("=== A. 手点 quad 对称不变量（真实截图直接测量，图片 px）===")
for slot, q0 in QUADS.items():
    q = order_diamond(np.array(q0, dtype=np.float32))
    inv = invariants(q)
    print(f"{slot}: W={inv['W']:.1f} H={inv['H']:.1f} W/H={inv['ratio_wh']:.3f} "
          f"d_h/d_v={inv['diag_ratio']:.3f} | "
          f"T_x-m_x={inv['Tx-mx']:+.1f} B_x-m_x={inv['Bx-mx']:+.1f} "
          f"mid(T_y,B_y)-m_y={inv['midTy-my']:+.1f}")

print()
print("=== B. 尺度敏感性：detect_village_quad 结果（s=1.0 真实；其余重采样模拟）===")
hdr = f"{'阵':<14} {'s':>4} {'方法':<16} {'置信':>6} {'检出':>4} {'残差均值px':>9} {'残差最大px':>9} {'残差均值格':>9} {'残差最大格':>9} {'检出W/H':>8} {'手点W/H':>8}"
print(hdr)
for slot, q0 in QUADS.items():
    b = BOUNDS[slot + ".png"]
    L, T, R, B = b["L"], b["T"], b["R"], b["B"]
    img = cv2.imread(os.path.join(BASE, slot + ".png"))
    assert img is not None, slot
    surf = img[T:B, L:R]
    q = order_diamond(np.array(q0, dtype=np.float32))
    hand_ratio = bbox_wh(q)[0] / bbox_wh(q)[1]
    n_ok = 0
    for s in SCALES:
        frame = cv2.resize(surf, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
        qs = q * s
        calib, meta = detect_village_quad(frame, grid_n=44)
        method = meta.get("method")
        conf = meta.get("confidence")
        dq = meta.get("quad")
        if dq is not None:
            dq = order_diamond(np.array(dq, dtype=np.float32))
            d = np.linalg.norm(dq - qs, axis=1)
            res_px = float(d.mean())
            res_max = float(d.max())
            dv = float(np.linalg.norm(qs[2] - qs[0]))
            dh = float(np.linalg.norm(qs[1] - qs[3]))
            pitch = ((dv + dh) / 2) / 44.0
            res_t = res_px / pitch
            res_t_max = res_max / pitch
            dratio = bbox_wh(dq)[0] / bbox_wh(dq)[1]
            n_ok += 1
        else:
            res_px = res_max = res_t = res_t_max = dratio = None
        def f(v, n=1):
            return f"{v:>{n}.2f}" if v is not None else f"{'—':>{n}}"
        conf_s = f"{conf:.3f}" if conf is not None else "—"
        print(f"{slot:<14} {s:>4.2f} {method:<16} {conf_s:>6} "
              f"{'是' if dq is not None else '否':>4} "
              f"{f(res_px,9)} {f(res_max,9)} {f(res_t,9)} {f(res_t_max,9)} "
              f"{f(dratio,8)} {hand_ratio:>8.3f}")
    print(f"  -> {slot} 检出 {n_ok}/5")

print()
print("=== C. 宽高比随缩放（手点 quad，均匀缩放不变量数值验证）===")
for slot, q0 in QUADS.items():
    q = order_diamond(np.array(q0, dtype=np.float32))
    ratios = []
    for s in SCALES:
        ratios.append(bbox_wh(q * s)[0] / bbox_wh(q * s)[1])
    print(f"{slot}: " + " ".join(f"{r:.4f}" for r in ratios))

print()
print("=== D. 若仅靠纵向非均匀压缩把 W/H 拉到 2.0，所需 H 系数 k=r/2.0 ===")
for slot, q0 in QUADS.items():
    q = order_diamond(np.array(q0, dtype=np.float32))
    r = bbox_wh(q)[0] / bbox_wh(q)[1]
    print(f"{slot}: r={r:.3f}  k(H×)={r/2.0:.3f}  (即纵向需压到 {r/2.0*100:.1f}%)")
