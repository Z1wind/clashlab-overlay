# -*- coding: utf-8 -*-
"""P2 临时 staging：15 号 Qembzi -> out/prebattle/info.json + layout_candidates.json。
仅 staging 全局运行时文件；P3 正式产物在 bases/th16/war_20261123/<slot>/prebattle/。
dps 由 load_local 经 assets.stats(th=16) 覆盖；此处 info.json dps 仅兜底。"""
import json, os
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 手工选点（图片 px）经 15 号 quad 反算 tile；负坐标夹到 0
exposed = [
    {"type": "eagle-artillery", "tile": [0, 9],  "dps": 350, "edge_dist": 6, "px": [406, 160], "note": "左上金红鹰炮（人工读点，tile 待实机复核）"},
    {"type": "air-defense",     "tile": [26, 3], "dps": 330, "edge_dist": 5, "px": [727, 274], "note": "右侧中部三联防空（人工读点）"},
    {"type": "scattershot",     "tile": [36, 9], "dps": 290, "edge_dist": 4, "px": [763, 360], "note": "右侧散射炮（人工读点）"},
    {"type": "inferno-tower",   "tile": [0, 30], "dps": 250, "edge_dist": 5, "px": [227, 289], "note": "左侧地狱塔（人工读点，类型待复核）"},
    {"type": "x-bow",           "tile": [32, 31],"dps": 200, "edge_dist": 6, "px": [521, 460], "note": "底部中部 X 连弩（人工读点，类型待复核）"},
    {"type": "town-hall",       "tile": [17, 16],"dps": 0,   "edge_dist": 0, "px": [521, 296], "note": "中心大本营（人工读点）"},
]
info = {
    "th": 16,
    "layout_id": "war_20261123_15_qembzi",
    "defense_counts": {"eagle-artillery": 1, "air-defense": 1, "scattershot": 1,
                       "inferno-tower": 1, "x-bow": 1, "town-hall": 1},
    "wall_level": "",
    "core_cover_dps": None,
    "centroid": [18.0, 18.0],
    "exposed": exposed,
    "blind": [],
    "enemy_hero_levels": {"queen": None, "king": None, "warden": None, "rc": None},
    "enemy_cc": None,
    "our_profile": {},
    "our_army": {},
    "unknown": [
        "th16_real_dps_pending_assets_override",
        "building_types_manual_read_pending_live_recheck",
        "tile_coords_approx_from_manual_quad",
        "enemy_hero_levels_unknown", "enemy_cc_troops_unknown", "trap_positions_unknown",
        "source:war_20261123/15_qembzi.png"
    ],
}
os.makedirs(os.path.join(ROOT, "out", "prebattle"), exist_ok=True)
with open(os.path.join(ROOT, "out", "prebattle", "info.json"), "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2)

# layout_candidates.json：quad 用 render 1280x720（15 号手工 quad 经 P0 归一化）
cand = {
    "version": 1,
    "source": "war_20261123/15_qembzi.png",
    "quad": [[628.0, 80.6], [1137.2, 399.0], [628.0, 684.9], [101.1, 412.0]],
    "candidates": [],
}
os.makedirs(os.path.join(ROOT, "out", "overlay"), exist_ok=True)
with open(os.path.join(ROOT, "out", "overlay", "layout_candidates.json"), "w", encoding="utf-8") as f:
    json.dump(cand, f, ensure_ascii=False, indent=2)
print("staged 15: info.json + layout_candidates.json")
