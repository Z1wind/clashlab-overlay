# -*- coding: utf-8 -*-
import unittest
from clashlab.overlay.pages import _opponent_th_suffix

class T(unittest.TestCase):
    def test_suffix(self):
        s = _opponent_th_suffix({"clan_th_dist": {16: 3, 15: 5, 14: 1, 13: 2}})
        self.assertIn("TH16×3", s)
        self.assertIn("TH15×5", s)
        self.assertNotIn("TH13", s)  # 只取前三

    def test_empty(self):
        self.assertEqual(_opponent_th_suffix({}), "")
        self.assertEqual(_opponent_th_suffix(None), "")
        self.assertEqual(_opponent_th_suffix({"clan_th_dist": None}), "")

if __name__ == "__main__":
    unittest.main()
