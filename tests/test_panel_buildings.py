# -*- coding: utf-8 -*-
"""面板「建筑构成」行测试。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LAY = {"name": "th16_03", "grid": 44,
       "buildings": [{"type": "town-hall", "tile": [21, 21], "level": 16},
                     {"type": "cannon", "tile": [3, 3], "level": 21},
                     {"type": "gold-mine", "tile": [30, 30], "level": 17},
                     {"type": "army-camp", "tile": [35, 35], "level": 14},
                     {"type": "bomb", "tile": [10, 10], "level": 11}],
       "walls": [[1, 1], [2, 1]]}


class TestPanelBuildings(unittest.TestCase):
    def test_fmt_counts(self):
        from clashlab.overlay import pages
        line = pages._fmt_buildings_counts({"total": 3, "defense": 1, "economy": 1, "walls": 5,
                                            "maxed_pct": 66})
        self.assertIn("防御 1", line)
        self.assertIn("经济 1", line)
        self.assertIn("墙 5", line)
        self.assertIn("66%", line)

    def test_fmt_empty(self):
        from clashlab.overlay import pages
        self.assertEqual(pages._fmt_buildings_counts({}), "建筑：无数据")

    def test_count_and_line(self):
        from clashlab.overlay import pages
        counts = pages._count_buildings(LAY)
        self.assertEqual(counts["total"], 5)
        self.assertEqual(counts["walls"], 2)
        self.assertEqual(counts["economy"], 1)
        self.assertEqual(counts["trap"], 1)
        self.assertEqual(counts["army"], 1)

    def test_line_from_state(self):
        from types import SimpleNamespace
        from clashlab.overlay import pages
        line = pages._buildings_line(SimpleNamespace(layout=LAY))
        self.assertIn("建筑：", line)
        self.assertIn("防御", line)

    def test_line_no_layout(self):
        from types import SimpleNamespace
        from clashlab.overlay import pages
        self.assertEqual(pages._buildings_line(SimpleNamespace(layout=None)), "建筑：无数据")


if __name__ == "__main__":
    unittest.main()
