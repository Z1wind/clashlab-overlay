# -*- coding: utf-8 -*-
"""城墙对称推理测试。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWallSymmetry(unittest.TestCase):
    def test_best_symmetry_from_buildings(self):
        from clashlab.wall_symmetry import best_symmetry
        pts = [(2, 2), (7, 2), (2, 5), (7, 5)]  # grid=10，左右对称
        name, score = best_symmetry(pts, grid=10)
        self.assertEqual(name, "mirror-x")
        self.assertGreaterEqual(score, 0.9)

    def test_infer_completes_right_side(self):
        from clashlab.wall_symmetry import infer_walls
        walls = [[3, 2], [3, 3], [3, 4]]
        info = infer_walls(walls, grid=10, ref_points=[(2, 2), (7, 2), (2, 5), (7, 5)])
        self.assertEqual(info["symmetry"], "mirror-x")
        self.assertIn((6, 2), info["inferred"])
        self.assertEqual(info["inferred_count"], 3)

    def test_rot180(self):
        from clashlab.wall_symmetry import best_symmetry
        pts = [(0, 0), (9, 9), (2, 7), (7, 2)]
        name, _ = best_symmetry(pts, grid=10)
        self.assertEqual(name, "rot180")

    def test_asymmetric_untouched(self):
        from clashlab.wall_symmetry import infer_walls
        walls = [[1, 1], [4, 6], [8, 2]]
        info = infer_walls(walls, grid=10, ref_points=[(1, 1), (4, 6), (8, 2)])
        self.assertEqual(info["symmetry"], "none")
        self.assertEqual(info["inferred_count"], 0)

    def test_components(self):
        from clashlab.wall_symmetry import main_walls, independent_walls
        walls = [[1, 1], [2, 1], [3, 1], [9, 9]]
        self.assertEqual(len(main_walls(walls)), 3)
        self.assertEqual(independent_walls(walls), [(9, 9)])

    def test_apply_symmetry_meta(self):
        from clashlab.wall_symmetry import apply_symmetry
        lay = {"grid": 10,
               "buildings": [{"type": "cannon", "tile": [2, 2]}, {"type": "cannon", "tile": [7, 2]},
                             {"type": "cannon", "tile": [2, 5]}, {"type": "cannon", "tile": [7, 5]}],
               "walls": [[3, 2], [3, 3], [3, 4]]}
        out = apply_symmetry(lay)
        self.assertGreater(len(out["walls"]), len(lay["walls"]))
        self.assertEqual(out["meta"]["wall_symmetry"]["symmetry"], "mirror-x")
        self.assertEqual(lay["walls"], [[3, 2], [3, 3], [3, 4]])  # 原对象不变


if __name__ == "__main__":
    unittest.main()
