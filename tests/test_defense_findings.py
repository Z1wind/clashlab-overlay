# -*- coding: utf-8 -*-
"""P3b-3 布局弱点 → 战术输出：RED 测试。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _layout(ad=True, th=(21, 21)):
    # 注意：箭塔/X连弩也算对空，所以要测「完全没有对空」必须只用纯对地防御（加农炮/迫击炮/炸弹塔）。
    bs = [{"type": "town-hall", "tile": list(th)},
          {"type": "cannon", "tile": [25, 25]},
          {"type": "mortar", "tile": [17, 27]}]
    if ad:
        bs.append({"type": "air-defense", "tile": [18, 18]})
    return {"name": "t", "grid": 44, "buildings": bs, "walls": []}


class TestFindings(unittest.TestCase):
    def test_no_layout_or_empty(self):
        from clashlab.defense_findings import findings, summary_line
        self.assertEqual(findings(None), [])
        self.assertEqual(findings({"name": "x", "grid": 44}), [])
        self.assertEqual(summary_line([]), "")

    def test_no_air_defense_flagged(self):
        from clashlab.defense_findings import findings
        fs = findings(_layout(ad=False))
        keys = [f["key"] for f in fs]
        self.assertIn("air-coverage", keys)
        air = [f for f in fs if f["key"] == "air-coverage"][0]
        self.assertIn("0%", air["text"])
        self.assertEqual(air["severity"], "critical")

    def test_town_hall_bias_direction(self):
        from clashlab.defense_findings import findings
        # TH 放左上角 -> 方位 north/west 之一，且出现大本营条目
        fs = findings(_layout(th=(4, 4)))
        th = [f for f in fs if f["key"] == "town-hall-protection"]
        self.assertTrue(th, "偏远大本营应产出条目")
        self.assertTrue(any(s in th[0]["text"] for s in ("north", "west", "北", "西")))
        # 居中的大本营不应报偏心
        fs2 = findings(_layout(th=(21, 21)))
        th2 = [f for f in fs2 if f["key"] == "town-hall-protection"]
        self.assertFalse(th2 and "偏" in th2[0]["text"] and th2[0]["severity"] == "weak")

    def test_summary_line_mentions_coverage(self):
        from clashlab.defense_findings import findings, summary_line
        line = summary_line(findings(_layout(ad=False)))
        self.assertIn("对空", line)
        self.assertIsInstance(line, str)


if __name__ == "__main__":
    unittest.main()
