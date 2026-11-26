# -*- coding: utf-8 -*-
"""2D 化模块测试。"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LAY = {"name": "t", "grid": 44,
       "buildings": [{"type": "town-hall", "tile": [21, 21]},
                     {"type": "cannon", "tile": [18, 18]},
                     {"type": "gold-storage", "tile": [25, 25]}],
       "walls": [[14, 14], [15, 14], [16, 14]]}


class TestTopdown(unittest.TestCase):
    def test_render_png(self):
        from clashlab.topdown import render_topdown
        d = tempfile.mkdtemp()
        p = os.path.join(d, "t.png")
        w, h, nb, nw = render_topdown(LAY, p, cell=12)
        # 新画布 = 地图 + 左右 margin 26*2 + 顶部标题栏 54 + 底部图例带 40
        margin, hud_h, legend_h = 26, 54, 40
        self.assertEqual((w, h), (44 * 12 + margin * 2, 44 * 12 + margin + hud_h + legend_h))
        self.assertEqual((nb, nw), (3, 3))
        self.assertGreater(os.path.getsize(p), 1000)

    def test_export_json(self):
        from clashlab.topdown import export_2d_json
        d = tempfile.mkdtemp()
        p = os.path.join(d, "t.json")
        doc = export_2d_json(LAY, p)
        self.assertEqual(doc["schema"], "clashlab-2d-v1")
        self.assertEqual(doc["grid"]["width"], 44)
        self.assertEqual(len(doc["objects"]), 3)
        self.assertEqual(doc["objects"][0]["category"], "town-hall")
        self.assertEqual(len(doc["walls"]), 3)
        loaded = json.load(open(p, encoding="utf-8"))
        self.assertEqual(loaded["objects"][1]["type"], "cannon")


if __name__ == "__main__":
    unittest.main()
