# -*- coding: utf-8 -*-
"""穿云箭自动选线测试：端点在地图内、优先吹风机。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 一条线能串吹风机+2 防空；另一条线只串 3 防空（无吹风机）
LAY = {"grid": 44, "buildings": [
    {"type": "air-sweeper", "tile": [10, 22]},
    {"type": "air-defense", "tile": [20, 22]},
    {"type": "air-defense", "tile": [30, 22]},
    {"type": "air-defense", "tile": [5, 8]},
    {"type": "air-defense", "tile": [10, 12]},
    {"type": "air-defense", "tile": [15, 16]},
]}


class TestArrowOptimizer(unittest.TestCase):
    def test_endpoints_inside_grid(self):
        from clashlab.overlay import giant_arrow_diagram as g
        res = g.optimize_giant_arrow(LAY, grid=44, top=8)
        self.assertTrue(res["candidates"])
        for c in res["candidates"]:
            for pt in (c["from"], c["to"]):
                self.assertGreaterEqual(pt[0], -0.01)
                self.assertLessEqual(pt[0], 44.01)
                self.assertGreaterEqual(pt[1], -0.01)
                self.assertLessEqual(pt[1], 44.01)

    def test_prefers_sweeper_line(self):
        from clashlab.overlay import giant_arrow_diagram as g
        best = g.optimize_giant_arrow(LAY, grid=44, top=5)["best"]
        self.assertIsNotNone(best)
        self.assertGreaterEqual(best["summary"]["air_sweeper"], 1)
        self.assertGreaterEqual(best["summary"]["air_defense"], 2)

    def test_score_prefers_sweeper(self):
        from clashlab.overlay import giant_arrow_diagram as g
        sweep = g.score_hits([{"type": "air-sweeper"}, {"type": "air-defense"}])
        ads = g.score_hits([{"type": "air-defense"}, {"type": "air-defense"}])
        self.assertGreater(sweep, ads)

    def test_clip_within(self):
        from clashlab.overlay import giant_arrow_diagram as g
        seg = g._clip_line((-10, 22), (50, 22), 44)
        self.assertIsNotNone(seg)
        self.assertEqual(seg[0][1], 22)
        self.assertGreaterEqual(min(seg[0][0], seg[1][0]), 0)
        self.assertLessEqual(max(seg[0][0], seg[1][0]), 44)


if __name__ == "__main__":
    unittest.main()
