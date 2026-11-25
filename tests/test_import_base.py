# -*- coding: utf-8 -*-
"""import_base 冒烟测试：合成草地菱形图 -> 自动标定 -> 产出 base/layout_draft/grid 三个文件。"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_synthetic(path):
    import cv2
    import numpy as np
    img = np.zeros((720, 1280, 3), np.uint8)
    # 背景草地绿
    img[:] = (60, 140, 70)
    # 中央菱形（等距）稍亮的草地
    pts = np.array([[640, 120], [1160, 360], [640, 600], [120, 360]], np.int32)
    cv2.fillPoly(img, [pts], (90, 170, 100))
    cv2.imencode(".png", img)[1].tofile(path)


class TestImportBase(unittest.TestCase):
    def test_import_from_synthetic_file(self):
        from tools.import_base import main
        d = tempfile.mkdtemp(prefix="imp_")
        shot = os.path.join(d, "shot.png")
        _make_synthetic(shot)
        out_base = os.path.join(d, "base07")
        argv = ["--th", "16", "--id", "07", "--from-file", shot, "--out-base", out_base]
        try:
            main(argv)
        except SystemExit as e:
            self.fail("import_base 退出: %r" % (e,))
        self.assertTrue(os.path.exists(os.path.join(out_base, "base.png")))
        lay_path = os.path.join(out_base, "layout_draft.json")
        self.assertTrue(os.path.exists(lay_path))
        lay = json.load(open(lay_path, encoding="utf-8"))
        self.assertEqual(lay["grid"], 44)
        self.assertIn("quad=", lay["note"])
        self.assertTrue(os.path.exists(os.path.join(ROOT, "out", "import", "07_grid.png")))


if __name__ == "__main__":
    unittest.main()
