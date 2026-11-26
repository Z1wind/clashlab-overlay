# -*- coding: utf-8 -*-
"""穿云箭：吹风机/防空火箭都应算对空目标；特斯拉默认隐身单独标记。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LAY = {"grid": 44, "buildings": [
    {"type": "air-defense", "tile": [10, 10]},
    {"type": "air-sweeper", "tile": [12, 10]},
    {"type": "hidden-tesla", "tile": [14, 10]},
    {"type": "cannon", "tile": [16, 10]},
    {"type": "gold-mine", "tile": [30, 30]},
]}


class TestGiantArrowAir(unittest.TestCase):
    def test_match_flags_air_and_hidden(self):
        from clashlab.overlay import giant_arrow_diagram as g
        hits = g.match_skewered(LAY, (0, 10), (20, 10), tol=1.2)
        by = {h["type"]: h for h in hits}
        self.assertTrue(by["air-defense"]["air"])
        self.assertTrue(by["air-sweeper"]["air"])
        self.assertTrue(by["hidden-tesla"]["hidden"])
        self.assertFalse(by["cannon"]["air"])

    def test_summary_counts(self):
        from clashlab.overlay import giant_arrow_diagram as g
        hits = g.match_skewered(LAY, (0, 10), (20, 10), tol=1.2)
        s = g.summarize_hits(hits)
        self.assertEqual(s["air_defense"], 1)
        self.assertEqual(s["air_sweeper"], 1)
        self.assertEqual(s["air_total"], 2)
        self.assertEqual(s["tesla_hidden"], 1)
        self.assertEqual(s["total"], len(hits))

    def test_order_is_along_arrow(self):
        from clashlab.overlay import giant_arrow_diagram as g
        hits = g.match_skewered(LAY, (0, 10), (20, 10), tol=1.2)
        self.assertEqual(hits, sorted(hits, key=lambda h: h["t"]))
        self.assertEqual([h["order"] for h in hits], list(range(1, len(hits) + 1)))


if __name__ == "__main__":
    unittest.main()
