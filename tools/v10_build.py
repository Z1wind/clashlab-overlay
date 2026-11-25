# -*- coding: utf-8 -*-
# v10_build.py — 组装交付：base/grid 图、collect_log meta、stitch_report（单帧现实：相机锁定无法6块）。
import cv2, numpy as np, os, json, time
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
FULL = os.path.join(ROOT, "out", "overlay", "full")

base = cv2.imdecode(np.fromfile(os.path.join(FULL, "b00.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
H, W = base.shape[:2]

# --- v10_full_base.png（已裁UI的唯一可用帧）---
cv2.imencode(".png", base)[1].tofile(os.path.join(FULL, "v10_full_base.png"))

# --- v10_full_grid.png：叠 44x44 晶格（沿用 v2 prior 晶格 O/a/b 作参考网，非拟合）---
grid = base.copy()
# v2 prior（来自 config/view_quads.json L0_snapped_v2，单帧内定位仅作参考网格）
O = np.array([473.2, 796.6])  # 注意：该原点属旧画布，此处仅示意网格方向
a = np.array([11.787, 20.906]); b = np.array([-20.337, 12.744])
# 以 b00 中心为临时原点铺等距参考网（方向用 prior）
Oc = np.array([W/2, H/2])
for i in range(-30, 31):
    p0 = Oc + i*a - 20*b; p1 = Oc + i*a + 30*b
    cv2.line(grid, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 180, 0), 1)
for j in range(-30, 31):
    p0 = Oc - 20*a + j*b; p1 = Oc + 30*a + j*b
    cv2.line(grid, tuple(p0.astype(int)), tuple(p1.astype(int)), (0, 180, 0), 1)
cv2.imencode(".png", grid)[1].tofile(os.path.join(FULL, "v10_full_grid.png"))

# --- collect_log.json 补 meta ---
LOG = os.path.join(FULL, "collect_log.json")
log = json.load(open(LOG, encoding="utf-8"))
log["meta"] = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "environment_note": (
        "重启后家景相机锁定：sendevent/input swipe 四向平移各仅约125px即边界；"
        "pinch-in(小/大展开)与鼠标滚轮均无缩放，pinch-out 有效；"
        "故2列x3行六块网格在本环境不可执行，仅得 b00 单帧。"
    ),
    "canvas_px": [W, H],
    "canvas_tiles_at24": [round(W/24, 1), round(H/24, 1)],
    "planned_grid": "2 cols x 3 rows, overlap>=35%",
    "captured_blocks": 1,
}
json.dump(log, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- stitch_report.json：单帧无内缝 ---
report = {
    "overlap": None,
    "max_seam_px": 1.0,
    "tile_size": [W, H],
    "grid": [1, 1],
    "blocks_captured": 1,
    "blocks_planned": 6,
    "seams": [],
    "seam_resid_px": [],
    "all_pass": None,
    "note": "相机锁定无法采集6块；单帧无内缝可校。详见 collect_log.meta。",
    "canvas_px": [W, H],
    "canvas_tiles_at24": [round(W/24, 1), round(H/24, 1)],
    "tile_px_criteria": log["blocks"][0]["tile_px"],
    "tile_px_est": log["blocks"][0]["tile_px_est"],
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
}
json.dump(report, open(os.path.join(FULL, "stitch_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("base/grid/log/report written", W, H)
