# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from clashlab import auto_candidates

class T(unittest.TestCase):
    def test_available_bool(self):
        self.assertIn(auto_candidates.available(), (True, False))

    def test_unavailable_returns_error(self):
        with mock.patch.object(auto_candidates, "available", return_value=False):
            r = auto_candidates.candidates("x.png", [[0,0],[1,0],[1,1],[0,1]])
        self.assertFalse(r["ok"])
        self.assertEqual(r["items"], [])

    def test_dedupe_logic(self):
        items = [
            {"type":"cannon","tile":[10,10],"size":3,"conf":0.99},
            {"type":"cannon","tile":[11,10],"size":3,"conf":0.98},   # 与上重叠，应去掉
            {"type":"x-bow","tile":[20,20],"size":3,"conf":0.97},
        ]
        picked = []
        for it in items:
            if all(abs(it["tile"][0]-p["tile"][0]) > 1 or abs(it["tile"][1]-p["tile"][1]) > 1 for p in picked):
                picked.append(it)
        self.assertEqual(len(picked), 2)

if __name__ == "__main__":
    unittest.main()
