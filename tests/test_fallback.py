# -*- coding: utf-8 -*-
"""test_fallback.py —— 兜底 payload：三段式标题 + 自带合法 格(x,y) 可被解析。

被测版本快照（详见 tests/README.md）：
  clashlab/overlay/tactics.py  mtime 2026-11-24 14:35:09
    sha256 758F854B73F3A8441333DA54A12BD0EE1FCCA1EF36035751F4284FE4EADBA6CC

两条路径都验：
  1) 代码自产兜底文本：tactics._local_fallback_text(doc) -> parse_plan_marks；
  2) 手工构造同型兜底 payload（三段式标题 + 自带合法格(x,y)）-> parse_plan_marks。
纯离线，不调 llm、不写盘。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clashlab.overlay import tactics


def _doc(rows):
    return {
        "ok": True, "source": "prebattle/info.json", "rows": rows,
        "blind": [], "counts": {}, "core_cover_dps": None,
        "centroid": None, "layout_id": "", "th": 14,
    }


ROWS = [
    {"type": "eagle-artillery", "name": "鹰炮", "tile": [36.0, 9.0],
     "dps": 420, "edge_dist": 1, "rank": 3},
    {"type": "air-defense", "name": "防空塔", "tile": [15.0, 30.0],
     "dps": 300, "edge_dist": 3, "rank": 3},
    {"type": "wizard-tower", "name": "法师塔", "tile": [25.0, 12.0],
     "dps": 240, "edge_dist": 5, "rank": 2},
]


class TestFallbackPayload(unittest.TestCase):
    def test_code_generated_fallback_text_parses(self):
        """_local_fallback_text 产出的三段式兜底文本，parse_plan_marks 抽出威胁/路线点。"""
        text = tactics._local_fallback_text(_doc(ROWS), goal="三星")
        self.assertIn("【威胁排序】", text)
        self.assertIn("【进攻路线】", text)
        self.assertIn("【兵种与法术】", text)

        out = tactics.parse_plan_marks({"text": text})
        threats = out["threats"]
        self.assertEqual(len(threats), 3, f"threats={threats}")
        self.assertEqual([t["label"] for t in threats], ["鹰炮", "防空塔", "法师塔"])
        self.assertEqual([t["tile"] for t in threats],
                         [[36, 9], [15, 30], [25, 12]])
        self.assertEqual([t["rank"] for t in threats], [1, 2, 3])

        route = out["route"]
        self.assertGreaterEqual(len(route), 3)
        self.assertEqual(route[0]["label"], "鹰炮")
        self.assertEqual(route[0]["tile"], [36, 9])
        self.assertEqual([r["seq"] for r in route[:3]], [1, 2, 3])

    def test_hand_built_fallback_payload_parses(self):
        """手工兜底 payload：三段式标题齐全，自带合法 格(x,y)，坐标值正确。"""
        text = (
            "【威胁排序】大本营 格(20,20)（dps 360）；防空塔 格(15,30)（dps 300）。\n"
            "【进攻路线】按 dps 降序清边后拆除：大本营 格(20,20) → 防空塔 格(15,30)；"
            "核心覆盖重区先绕边清掉再进。\n"
            "【兵种与法术】本地规则建议：先清边铺主力，高 dps 点用法术配合拆除；"
            "具体配比待联网模型复核。\n"
            "（目标：三星；本段为本地规则分析，非大模型生成）"
        )
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual([t["label"] for t in out["threats"]], ["大本营", "防空塔"])
        self.assertEqual([t["tile"] for t in out["threats"]], [[20, 20], [15, 30]])
        self.assertEqual([t["rank"] for t in out["threats"]], [1, 2])
        self.assertEqual([r["label"] for r in out["route"]], ["大本营", "防空塔"])
        self.assertEqual([r["tile"] for r in out["route"]], [[20, 20], [15, 30]])
        self.assertEqual([r["seq"] for r in out["route"]], [1, 2])

    def test_empty_rows_fallback_has_no_false_marks(self):
        """无外露防御的兜底文本（无合法坐标）：解析为空，不编造标注点，不抛异常。"""
        text = tactics._local_fallback_text(_doc([]), goal="三星")
        out = tactics.parse_plan_marks({"text": text})
        self.assertEqual(out["threats"], [])
        self.assertEqual(out["route"], [])


if __name__ == "__main__":
    unittest.main()
