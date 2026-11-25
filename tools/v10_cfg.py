# -*- coding: utf-8 -*-
# v10_cfg.py — 仅追加新键 L0_full；旧键一字节不动。
import json, os, datetime
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
P = os.path.join(ROOT, "config", "view_quads.json")
qj = json.load(open(P, encoding="utf-8"))
before = list(qj.keys())
qj["L0_full"] = {
  "quad": {"T": None, "R": None, "B": None, "L": None},
  "quad_note": "顶边出画、左右仅下段可见；四顶点无法由可见直边相交直读，不做外推。",
  "px_per_tile": 24.0,
  "px_per_tile_evidence": "v6_tile_px: edge_step=31.17 / fft_texture=24.0 / blob_spacing=14.02, est=24.0, consensus=False(edge-fft rel>15%); 模板链 s=1.00(corr0.677) 相对 zoom_L0 同尺度, tile_px=24.0",
  "H_W": None,
  "canvas": [865, 537],
  "canvas_tiles_at24": [36.0, 22.4],
  "verts_in_canvas": False,
  "seams": [],
  "blocks_captured": 1,
  "blocks_planned": 6,
  "status": "near",
  "gap": (
    "环境阻塞：重启后家景相机锁定，sendevent/input swipe 四向平移各仅约125px即到边界，"
    "pinch-in(小/大展开)与鼠标滚轮均无缩放、pinch-out有效；2列x3行六块网格与≥3格草地余量不可达；"
    "单帧36.0x22.4格<44x44，平台顶边出画，四顶点不全在画布。"
  ),
  "attack_button_tapped": False,
  "ts": datetime.datetime.now().isoformat(timespec="seconds"),
}
json.dump(qj, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
chk = json.load(open(P, encoding="utf-8"))
after = list(chk.keys())
print("before keys:", before)
print("after  keys:", after)
print("added:", [k for k in after if k not in before])
assert all(k in after for k in before), "旧键丢失!"
