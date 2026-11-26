# -*- coding: utf-8 -*-
"""英雄落点 → 最近目标 → 穿云箭方向 & 敏感性测试。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LAY = {"grid": 44, "buildings": [
    {"type": "air-defense", "tile": [20, 10]},
    {"type": "cannon", "tile": [20, 30]},
]}
FLIP = {"grid": 44, "buildings": [
    {"type": "air-defense", "tile": [20, 11]},
    {"type": "cannon", "tile": [20, 9]},
]}


class TestArrowPlacement(unittest.TestCase):
    def test_nearest_is_center_distance(self):
        from clashlab.overlay import arrow_placement as ap
        tgt = ap.nearest_building(LAY, [20, 8.5])
        self.assertEqual(tgt["type"], "air-defense")
        tgt2 = ap.nearest_building(LAY, [20, 28])
        self.assertEqual(tgt2["type"], "cannon")

    def test_arrow_direction_points_to_target(self):
        from clashlab.overlay import arrow_placement as ap
        res = ap.arrow_from_placement(LAY, [20, 8.5])
        self.assertEqual(res["target"]["type"], "air-defense")
        # 方向应指向 (20,10)：从 (20,8.5) 出发角度接近 90°
        self.assertAlmostEqual(res["angle_deg"], 90.0, delta=1.0)
        self.assertEqual(res["from"], [20.0, 8.5])
        self.assertGreater(res["to"][1], 8.5)

    def test_near_tie_flips_with_small_offset(self):
        from clashlab.overlay import arrow_placement as ap
        base = ap.arrow_from_placement(FLIP, [20, 10.0])
        moved = ap.arrow_from_placement(FLIP, [20.3, 10.0])
        sens = ap.placement_sensitivity(FLIP, [20, 10.0], radius=0.5, step=0.25)
        # 两个建筑中心几乎对称，微小横移就可能换目标 -> 必须报不稳定
        self.assertFalse(sens["stable"] or base["target"]["type"] == moved["target"]["type"]
                         and sens["distinct_signatures"] == 1)

    def test_stable_placement(self):
        from clashlab.overlay import arrow_placement as ap
        lay = {"grid": 44, "buildings": [{"type": "air-defense", "tile": [20, 4]},
                                         {"type": "monolith", "tile": [40, 40]}]}
        sens = ap.placement_sensitivity(lay, [20, 10], radius=0.5, step=0.25)
        self.assertTrue(sens["stable"])

    def test_hits_reported(self):
        from clashlab.overlay import arrow_placement as ap
        res = ap.arrow_from_placement(LAY, [20, 8.5])
        self.assertTrue(any(h["type"] == "air-defense" for h in res["hits"]))

    def test_corner_mode_shifts_center(self):
        from clashlab.overlay import arrow_placement as ap
        b = {"type": "air-defense", "tile": [10, 10]}
        c = ap.building_center(b, "corner")
        self.assertGreater(c[0], 10)
        self.assertGreater(c[1], 10)


if __name__ == "__main__":
    unittest.main()
