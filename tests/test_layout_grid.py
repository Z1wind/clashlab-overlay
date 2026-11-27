# -*- coding: utf-8 -*-
import unittest
from clashlab.layout_grid import LayoutGrid

SQUARE = [[2,2],[10,2],[10,10],[2,10],[2,2]]

class T(unittest.TestCase):
    def test_wall_rasterize_and_compartments(self):
        g = LayoutGrid.from_layout({"walls": SQUARE, "buildings": [{"type":"town-hall","tile":[6,6]}]})
        self.assertGreater(g.wall_count(), 20)
        comps = g.compartments(min_tiles=4)
        self.assertEqual(len(comps), 1)          # 正方形墙内一圈是闭合隔间
        self.assertTrue(any((6,6) in c for c in comps))
        self.assertTrue(g.th_inside_walls())

    def test_open_wall_no_compartment(self):
        g = LayoutGrid.from_layout({"walls": [[2,2],[10,2],[10,10]], "buildings": []})
        self.assertEqual(len(g.compartments(min_tiles=4)), 0)

    def test_empty(self):
        g = LayoutGrid.from_layout({"buildings": []})
        self.assertEqual(g.wall_count(), 0)
        self.assertEqual(g.compartments(), [])
        self.assertEqual(g.wall_efficiency(), 0.0)

    def test_validate_overlap(self):
        g = LayoutGrid.from_layout({"walls": [[0,0]], "buildings": [{"type":"cannon","tile":[0,0]}]})
        kinds = [i["kind"] for i in g.validate()]
        self.assertIn("wall-over-building", kinds)

if __name__ == "__main__":
    unittest.main()
