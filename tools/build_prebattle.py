# -*- coding: utf-8 -*-
"""P3：四套 prebattle/info.json（th=16）。
位置=人工读图 px 经本阵手工 quad px_to_tile；类型为最佳人工判读（confidence 标注）；
dps 留 null，运行时由 assets.stats(name, th=16) 取数，此处不写作废兜底值。
不确定/被遮挡栋一律进 unknown，不猜。"""
import os, sys, json
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab.geo import Calib

ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BASE = os.path.join(ROOT, "bases", "th16", "war_20261123")

# 手工 quad（图片像素）：T,R,B,L
QUADS = {
 "14_kekejdj": [[520,110],[905,345],[512,555],[150,350]],
 "15_qembzi":  [[512,110],[915,355],[512,575],[95,365]],
 "16_diddieyang": [[508,105],[925,365],[508,560],[95,360]],
 "17_akib":    [[500,105],[930,360],[500,565],[90,360]],
}
# 人工读点（图片 px）+ 最佳类型判读；confidence 为类型把握，非几何
PICKS = {
 "14_kekejdj": [
   ([468,327], "town-hall", 0.85, "中心红金大本营"),
   ([457,130], "scattershot", 0.45, "顶部旋转炮（类型待复核）"),
   ([309,249], "air-defense", 0.40, "左侧外圈橙炮（类型待复核）"),
   ([605,249], "air-defense", 0.40, "右侧外圈橙炮（类型待复核）"),
   ([468,474], "inferno-tower", 0.35, "底部中部建筑（类型待复核）"),
 ],
 "15_qembzi": [
   ([406,160], "eagle-artillery", 0.55, "左上金红鹰炮（人工读点）"),
   ([521,296], "town-hall", 0.80, "中心大本营"),
   ([727,274], "air-defense", 0.45, "右侧中部三联防空（人工读点）"),
   ([763,360], "scattershot", 0.45, "右侧散射炮（人工读点）"),
   ([227,289], "inferno-tower", 0.35, "左侧地狱塔（类型待复核）"),
   ([521,460], "x-bow", 0.35, "底部中部 X 连弩（类型待复核）"),
 ],
 "16_diddieyang": [
   ([439,341], "town-hall", 0.80, "中心大本营"),
   ([534,119], "clan-castle", 0.40, "顶部偏右紫色城堡（类型待复核）"),
   ([231,268], "air-defense", 0.40, "左侧外圈防空（类型待复核）"),
   ([653,246], "scattershot", 0.40, "右侧外圈散射炮（类型待复核）"),
   ([439,504], "x-bow", 0.35, "底部中部建筑（类型待复核）"),
 ],
 "17_akib": [
   ([439,327], "town-hall", 0.80, "中心大本营"),
   ([453,127], "eagle-artillery", 0.40, "顶部鹰炮（类型待复核）"),
   ([231,282], "air-defense", 0.40, "左侧外圈防空（类型待复核）"),
   ([653,268], "air-defense", 0.40, "右侧外圈防空（类型待复核）"),
   ([439,489], "inferno-tower", 0.35, "底部中部地狱塔（类型待复核）"),
 ],
}

for slot, quad in QUADS.items():
    cal = Calib.from_quad(quad, 44)
    exposed, counts = [], {}
    tx = ty = 0.0
    for (px, py), typ, conf, note in PICKS[slot]:
        gx, gy = cal.px_to_tile(px, py)
        gx = int(round(max(0, min(44, gx))))
        gy = int(round(max(0, min(44, gy))))
        exposed.append({
            "type": typ, "tile": [gx, gy], "dps": None,
            "edge_dist": None,
            "image_px": [px, py],
            "confidence": conf, "note": note,
            "source": "manual-read",
        })
        counts[typ] = counts.get(typ, 0) + 1
        tx += gx; ty += gy
    n = len(exposed) or 1
    info = {
        "th": 16,
        "layout_id": f"war_20261123_{slot}",
        "source_image": f"{slot}.png",
        "defense_counts": counts,
        "wall_level": "",
        "core_cover_dps": None,
        "centroid": [round(tx/n, 1), round(ty/n, 1)],
        "exposed": exposed,
        "blind": [],
        "enemy_hero_levels": {"queen": None, "king": None, "warden": None, "rc": None},
        "enemy_cc": None,
        "our_profile": {},
        "our_army": {},
        "unknown": [
            "building_types_manual_read_low_confidence_pending_live_recheck",
            "dps_pending_assets.stats(th=16)_runtime_fill",
            "enemy_hero_levels_unknown", "enemy_cc_troops_unknown",
            "trap_positions_unknown", "wall_level_unknown",
            "quad_manual_approx_pending_P2_live_calibration",
        ],
    }
    d = os.path.join(BASE, slot, "prebattle")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(slot, "exposed", n, "tiles", [(e["tile"], e["type"]) for e in exposed])
