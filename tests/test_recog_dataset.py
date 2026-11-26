# -*- coding: utf-8 -*-
"""识别数据集构建测试。"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRecogDataset(unittest.TestCase):
    def test_parse_quad(self):
        from clashlab.recog_dataset import parse_quad
        note = "TH16 quad=[[1288,12],[2314,569],[1281,1193],[282,562]] reproj_error=0.0"
        q = parse_quad(note)
        self.assertEqual(len(q), 4)
        self.assertEqual(q[0], [1288, 12])
        self.assertIsNone(parse_quad("no quad here"))
        self.assertIsNone(parse_quad(None))

    def test_build_dataset_real_base(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        p = os.path.join(root, "bases", "th16", "03", "layout.json")
        from clashlab.recog_dataset import build_dataset
        crops, labels, bases = build_dataset([p])
        lay = json.load(open(p, encoding="utf-8"))
        self.assertEqual(len(crops), len(lay["buildings"]))
        self.assertEqual(crops[0].shape, (96, 96, 3))
        self.assertTrue(all(b == "03" for b in bases))



    def test_parse_quad_with_labels(self):
        from clashlab.recog_dataset import parse_quad
        note = "quad(上,右,下,左)=[[500,12],[860,215],[500,456],[140,215]] reproj_error=0.0"
        q = parse_quad(note)
        self.assertEqual(len(q), 4)
        self.assertEqual(q[0], [500, 12])

    def test_load_annotations_with_override_priority(self):
        from clashlab.recog_dataset import load_layouts
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        paths = [os.path.join(root, "out", "annotate", "%02d_annotated.json" % i) for i in range(1, 7)]
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            self.skipTest("没有本地标注文件")
        loaded = load_layouts(paths)
        self.assertGreaterEqual(len(loaded), 1)
        for name, lay, img, calib in loaded:
            self.assertTrue(os.path.exists(img))
            self.assertIn("base.png", img)

if __name__ == "__main__":
    unittest.main()