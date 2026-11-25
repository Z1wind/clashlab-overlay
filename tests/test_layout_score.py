# -*- coding: utf-8 -*-
"""P3b-1 布局评分（移植 clash-blueprint-engine analyzer）的 RED 测试。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGradeAndGeometry(unittest.TestCase):
    def test_grade_bands(self):
        from clashlab.layout_score import grade_for
        self.assertEqual(grade_for(95), "S")
        self.assertEqual(grade_for(90), "S")
        self.assertEqual(grade_for(85), "A")
        self.assertEqual(grade_for(75), "B")
        self.assertEqual(grade_for(60), "C")
        self.assertEqual(grade_for(45), "D")
        self.assertEqual(grade_for(10), "F")

    def test_centrality_center_and_corner(self):
        from clashlab.layout_score import centrality
        self.assertAlmostEqual(centrality((22.0, 22.0), 44), 1.0, places=3)
        self.assertAlmostEqual(centrality((0.0, 0.0), 44), 0.0, places=3)

    def test_wall_ring_coverage_full_and_none(self):
        from clashlab.layout_score import wall_ring_coverage, footprint_bounds
        b = {"type": "eagle-artillery", "tile": [22, 22]}  # 3x3
        x0, y0, w, h = footprint_bounds(b)
        ring = []
        for x in range(x0 - 1, x0 + w + 1):
            ring += [[x, y0 - 1], [x, y0 + h]]
        for y in range(y0, y0 + h):
            ring += [[x0 - 1, y], [x0 + w, y]]
        self.assertGreater(wall_ring_coverage(b, ring), 0.95)
        self.assertEqual(wall_ring_coverage(b, []), 0.0)


class TestMetrics(unittest.TestCase):
    def _layout(self, buildings=None, walls=None):
        return {"name": "t", "grid": 44, "buildings": buildings or [], "walls": walls or []}

    def test_no_air_defense_is_critical_weak_point(self):
        from clashlab.layout_score import score_layout
        lay = self._layout([{"type": "town-hall", "tile": [21, 21]},
                            {"type": "cannon", "tile": [18, 18]}])
        out = score_layout(lay)
        air = [m for m in out["metrics"] if m["id"] == "air-coverage"][0]
        self.assertEqual(air["score"], 0.0)
        msgs = [w["message"] for w in out["weakPoints"]]
        self.assertTrue(any("防空" in m or "air" in m.lower() for m in msgs))
        self.assertTrue(any(w["severity"] == "critical" for w in out["weakPoints"]))

    def test_score_bounds_and_weight_sum(self):
        from clashlab.layout_score import score_layout, METRICS
        lay = self._layout([{"type": "town-hall", "tile": [21, 21]},
                            {"type": "air-defense", "tile": [18, 18]}])
        out = score_layout(lay)
        self.assertGreaterEqual(out["overall"], 0.0)
        self.assertLessEqual(out["overall"], 100.0)
        self.assertEqual(sum(m["weight"] for m in out["metrics"]), 13)
        self.assertEqual(len(out["metrics"]), 7)
        self.assertIn(out["grade"], list("SABCDF"))

    def test_enclosed_compartment_and_dead_zone(self):
        from clashlab.layout_score import analyze_compartments
        walls = []
        for x in range(10, 17):
            walls += [[x, 10], [x, 16]]
        for y in range(10, 17):
            walls += [[10, y], [16, y]]
        comp = analyze_compartments(44, walls, [])
        self.assertGreaterEqual(len(comp["compartments"]), 1)
        big = max(comp["compartments"], key=lambda c: c["tile_count"])
        self.assertTrue(big["is_dead_zone"])  # 空隔间 = 死区
        # 有一个 3x3 建筑中心在圈内则不是死区
        comp2 = analyze_compartments(44, walls, [{"type": "cannon", "tile": [13, 13]}])
        big2 = max(comp2["compartments"], key=lambda c: c["tile_count"])
        self.assertFalse(big2["is_dead_zone"])

    def test_wall_efficiency_isolated_walls(self):
        from clashlab.layout_score import wall_efficiency
        self.assertLess(wall_efficiency(44, [[5, 5]], 10), 60.0)  # 全孤立
        box = []
        for x in range(10, 16):
            box += [[x, 10], [x, 15]]
        for y in range(10, 16):
            box += [[10, y], [15, y]]
        inside = [{"type": "cannon", "tile": [12, 12]}]
        self.assertGreater(wall_efficiency(44, box, 1, inside), 50.0)


class TestRealBases(unittest.TestCase):
    def test_six_bases_scored(self):
        from clashlab.layout_score import score_layout, load_layout
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bases", "th16")
        found = 0
        for name in sorted(os.listdir(base_dir)):
            p = os.path.join(base_dir, name, "layout.json")
            if not os.path.exists(p):
                continue
            out = score_layout(load_layout(p))
            self.assertTrue(0 <= out["overall"] <= 100, name)
            self.assertEqual(len(out["metrics"]), 7, name)
            found += 1
        self.assertGreaterEqual(found, 5)


if __name__ == "__main__":
    unittest.main()
