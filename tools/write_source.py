# -*- coding: utf-8 -*-
"""任务1：6 图 source.json（尺寸/表面边界/用途/映射引用）。"""
import os, json, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\bases\th16\war_20261123"
BOUNDS = json.load(open(os.path.join(ROOT, "_verify", "frame_bounds.json"), encoding="utf-8"))["images"]
META = {
 "01_village_a.png": {"role": "村庄视图/复制阵型参考（非敌阵）", "enemy": None},
 "02_village_b.png": {"role": "村庄视图参考（非敌阵）", "enemy": None},
 "14_kekejdj.png": {"role": "部落战 14 号敌阵", "enemy": {"slot": 14, "name": "kekejdj", "clan": "WARRIORS"}},
 "15_qembzi.png": {"role": "部落战 15 号敌阵", "enemy": {"slot": 15, "name": "Qembzi", "clan": "WARRIORS"}},
 "16_diddieyang.png": {"role": "部落战 16 号敌阵", "enemy": {"slot": 16, "name": "Diddieyang", "clan": "WARRIORS"}},
 "17_akib.png": {"role": "部落战 17 号敌阵", "enemy": {"slot": 17, "name": "AKIB", "clan": "WARRIORS"}},
}
out = {"version": 1, "mapping_ref": "_verify/coord_mapping.md",
       "note": "整窗抓屏含 chrome；表面边界见 frame_bounds.json；图片坐标不可直接装覆盖层。",
       "images": []}
for fn, m in META.items():
    p = os.path.join(ROOT, fn)
    img = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    b = BOUNDS.get(fn, {})
    out["images"].append({
        "file": fn, "size": [w, h], "role": m["role"], "enemy": m["enemy"],
        "surface_bounds": {"L": b.get("L"), "T": b.get("T"), "R": b.get("R"), "B": b.get("B")},
    })
with open(os.path.join(ROOT, "source.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("source.json written", len(out["images"]))
