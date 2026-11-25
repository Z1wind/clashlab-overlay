# -*- coding: utf-8 -*-
"""v6_selftest.py — 拼接工具 + tile_px 函数的"切开→拼回"自验（纯离线）。

流程：
1. 读 15_qembzi.png，按 frame_bounds.json 剥 chrome 得纯净表面；
2. 人为切成 2×2、重叠 20% 的小块（模拟执行线分块）；
3. v6_stitch.stitch 自动估位移拼回；
4. 与原图逐像素差：max / median / 超4px占比；合格判定；
5. v6_tile_px 对原图与拼接图各测一次，比对一致性。
结果打印到控制台，不落分析文档。
"""
import os, sys, json
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from v6_stitch import stitch          # noqa: E402
from v6_tile_px import measure_tile_px  # noqa: E402

BASE = os.path.join(ROOT, "bases", "th16", "war_20261123")
OUT = os.path.join(HERE, "v6_out")
os.makedirs(OUT, exist_ok=True)

SLOT = "15_qembzi"
OVERLAP = 0.2
GRID = (2, 2)

# 1) 剥 chrome
with open(os.path.join(BASE, "_verify", "frame_bounds.json"), encoding="utf-8") as f:
    b = json.load(f)["images"][SLOT + ".png"]
L, T, R, B = b["L"], b["T"], b["R"], b["B"]
def imread_u(path):
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)

img = imread_u(os.path.join(BASE, SLOT + ".png"))
assert img is not None
surface = img[T:B, L:R]
H, W = surface.shape[:2]
print(f"表面尺寸 {W}×{H}（chrome 已剥：L{L} T{T} R{R} B{B}）")

# 2) 切 2×2 重叠20%（整数位置，保证末块到边）
rows, cols = GRID
tile_w = round(W / (cols - OVERLAP * (cols - 1)))
tile_h = round(H / (rows - OVERLAP * (rows - 1)))
stride_x = round(tile_w * (1 - OVERLAP))
stride_y = round(tile_h * (1 - OVERLAP))
xs = [c * stride_x for c in range(cols)]
ys = [r * stride_y for r in range(rows)]
xs[-1] = W - tile_w
ys[-1] = H - tile_h
tiles = []
for r in range(rows):
    for c in range(cols):
        tiles.append(surface[ys[r]:ys[r] + tile_h, xs[c]:xs[c] + tile_w])
print(f"分块 {len(tiles)}：块 {tile_w}×{tile_h}，步长 {stride_x}×{stride_y}，"
      f"重叠 {round(tile_w*OVERLAP)}×{round(tile_h*OVERLAP)}")

# 3) 拼接（不给位移，自动估）
report_path = os.path.join(OUT, "stitch_report.json")
canvas, report = stitch(tiles, offsets=None, overlap=OVERLAP, grid=GRID,
                         report_path=report_path)
cv2.imwrite(os.path.join(OUT, "stitched.png"), canvas)

# 4) 重建误差（公共区域对比，容忍亚像素精修带来的 1px 外扩）
ch, cw = canvas.shape[:2]
mh, mw = min(ch, H), min(cw, W)
print(f"画布 {cw}×{ch}，公共对比区 {mw}×{mh}")
diff = np.abs(canvas[:mh, :mw].astype(np.int16) - surface[:mh, :mw].astype(np.int16))
mad = np.median(diff)
mx = diff.max()
over4 = float((np.all(diff > 4, axis=2)).mean() * 100)
# 通道任一超4px也算（灰度口径补充）
over4_any = float((diff.max(axis=2) > 4).mean() * 100)
print("\n--- 重建误差（拼接图 vs 剥chrome原图）---")
print(f"max={mx}px  median={mad}px  全通道>4px占比={over4:.4f}%  任一通道>4px占比={over4_any:.4f}%")
print(f"缝校验：all_pass={report['all_pass']}")
for t in report["tiles"]:
    print(f"  块{t['index']}: dx={t['dx']:.2f} dy={t['dy']:.2f} "
          f"seam={t['seam_err_px']}px pass={t['pass']} need_rescan={t['need_rescan']} "
          f"orb_med={t['orb_med_px']} inliers={t['orb_inliers']} mad={t['overlap_mad']}")

# 5) tile_px 原图 vs 拼接图
m0 = measure_tile_px(surface)
m1 = measure_tile_px(canvas)
print("\n--- tile_px 测量（原图 vs 拼接图）---")
print("原图:    ", json.dumps(m0, ensure_ascii=False))
print("拼接图:  ", json.dumps(m1, ensure_ascii=False))
if m0["estimate"] and m1["estimate"]:
    rel = abs(m0["estimate"] - m1["estimate"]) / max(m0["estimate"], m1["estimate"])
    print(f"两图估值相对差={rel:.4f} ({'一致' if rel <= 0.15 else '不一致'})")
