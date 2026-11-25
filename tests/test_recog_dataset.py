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


if __name__ == "__main__":
    unittest.main()
