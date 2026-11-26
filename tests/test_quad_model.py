# -*- coding: utf-8 -*-
"""四角回归模型测试（无 torch / 无 checkpoint 时跳过）。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestQuadModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import torch  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("torch 未安装（可选推理依赖）")
        from clashlab.quad_model import CKPT
        if not os.path.exists(CKPT):
            raise unittest.SkipTest("四角模型 checkpoint 不存在，先跑 tools/train_quad_model.py")
        from clashlab.quad_model import load_model
        cls.model = load_model()

    def _img(self):
        import numpy as np
        return np.random.RandomState(3).randint(0, 256, (180, 320, 3), dtype=np.uint8)

    def test_predict_shape_and_order(self):
        q = self.model.predict(self._img())
        self.assertEqual(len(q), 4)
        for p in q:
            self.assertEqual(len(p), 2)

    def test_predict_deterministic(self):
        a = self.model.predict(self._img())
        b = self.model.predict(self._img())
        self.assertEqual(a, b)

    def test_predict_on_real_image(self):
        import cv2
        import numpy as np
        import glob
        files = glob.glob(os.path.join(ROOT, "out", "quad_images", "*.jpg"))
        if not files:
            self.skipTest("没有本地图片")
        img = cv2.imdecode(np.fromfile(files[0], np.uint8), cv2.IMREAD_COLOR)
        q = self.model.predict(img)
        for x, y in q:
            self.assertTrue(0 <= x <= img.shape[1] * 1.2)
            self.assertTrue(0 <= y <= img.shape[0] * 1.2)


if __name__ == "__main__":
    unittest.main()
