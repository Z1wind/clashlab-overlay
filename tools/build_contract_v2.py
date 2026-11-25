# -*- coding: utf-8 -*-
"""人工类型路径契约：位置来自引擎 high 候选，类型由人工下拉指定（edits 冻结）。
读 out/check_verify/frozen_layout.json（位置，弃引擎 type_guess），
应用 out/snap/annot/human_type_edits.json（人工逐条类型决定），
clamp tile 到 0..43，写 out/snap/contract_v2_layout.json，供 study/marks/prebattle。
不修改 gold、不修改引擎候选文件。
"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

frozen = json.load(open(os.path.join(ROOT, "out/check_verify/frozen_layout.json"), encoding="utf-8"))
edits = json.load(open(os.path.join(ROOT, "out/snap/annot/human_type_edits.json"), encoding="utf-8"))
# edits: [{index, tile, human_type, note}]，index 对齐 frozen.buildings 顺序
edit_map = {e["index"]: e for e in edits["entries"]}

out = {
    "name": "home_village_contract_v2_human_typed",
    "grid": 44,
    "source": "candidate_position_plus_human_type_edits",
    "note": "位置来自引擎 high 候选；引擎 type_guess 不进冻结，类型由人工 edits 指定；tile clamp 0..43。",
    "buildings": [],
}
for i, b in enumerate(frozen["buildings"]):
    e = edit_map.get(i)
    if e is None:
        raise SystemExit(f"missing human edit for index {i}")
    t = [max(0, min(43, int(round(v)))) for v in b["tile"]]
    out["buildings"].append({
        "tile": t,
        "type": e["human_type"],
        "size_tiles": b.get("size_tiles", 3),
        "human_note": e["note"],
    })
dst = os.path.join(ROOT, "out/snap/contract_v2_layout.json")
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("buildings", len(out["buildings"]), "->", os.path.relpath(dst, ROOT))
