# -*- coding: utf-8 -*-
"""放兵线/区域候选与优化测试。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LAY = {"name": "t", "grid": 20,
       "buildings": [{"type": "town-hall", "tile": [9, 9]},
                     {"type": "cannon", "tile": [4, 4]},
                     {"type": "archer-tower", "tile": [15, 15]}],
       "walls": []}


class TestDeploy(unittest.TestCase):
    def test_point_candidates(self):
        from clashlab.deploy import point_candidates
        cs = point_candidates(LAY)
        self.assertGreaterEqual(len(cs), 4)
        for c in cs:
            self.assertEqual(c["kind"], "point")
            self.assertEqual(len(c["points"]), 1)

    def test_line_candidates(self):
        from clashlab.deploy import line_candidates
        cs = line_candidates(LAY)
        self.assertEqual(len(cs), 12)
        for c in cs:
            self.assertEqual(len(c["points"]), 4)
            for x, y in c["points"]:
                self.assertTrue(0 <= x < LAY["grid"] and 0 <= y < LAY["grid"])

    def test_region_candidates(self):
        from clashlab.deploy import region_candidates
        cs = region_candidates(LAY)
        self.assertEqual(len(cs), 4)
        self.assertTrue(all(len(c["points"]) == 4 for c in cs))

    def test_multi_spawn_keeps_all_units(self):
        from clashlab import wargame
        one = wargame.simulate_once(LAY, {"giant": 6, "wizard": 8}, spawn=(1, 9), seed=1)
        multi = wargame.simulate_once(LAY, {"giant": 6, "wizard": 8},
                                      spawn=[(1, 9), (1, 12), (1, 15), (1, 18)], seed=1)
        self.assertEqual(one["units_total"], multi["units_total"])

    def test_optimize_schema_and_determinism(self):
        from clashlab.deploy import optimize
        a = optimize(LAY, {"giant": 4, "wizard": 4}, mode="line", trials=3, seed=2)
        b = optimize(LAY, {"giant": 4, "wizard": 4}, mode="line", trials=3, seed=2)
        self.assertEqual(a, b)
        self.assertIn("best", a)
        self.assertEqual(len(a["candidates"]), 12)
        for r in a["candidates"]:
            self.assertGreaterEqual(r["min"], 0)
            self.assertLessEqual(r["max"], 100)

    def test_optimize_modes(self):
        from clashlab.deploy import optimize
        for mode, n in (("point", 6), ("region", 4), ("all", 22)):
            res = optimize(LAY, {"giant": 2}, mode=mode, trials=1, seed=3)
            self.assertEqual(len(res["candidates"]), n)
            self.assertEqual(res["mode"], mode)


if __name__ == "__main__":
    unittest.main()
