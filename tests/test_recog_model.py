# -*- coding: utf-8 -*-
"""recog_model 推理接口测试：checkpoint 可加载 / 输出维度正确 / 推理可复现。"""
import os
import sys
import unittest

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CKPT = os.path.join(ROOT, "models", "recog_27px.pt")


class TestRecogModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(CKPT):
            raise AssertionError(
                "checkpoint 不存在：%s\n先跑 python tools/train_save_model.py" % CKPT)
        from clashlab.recog_model import load_model
        cls.model = load_model()

    def test_checkpoint_structure(self):
        self.assertTrue(os.path.exists(CKPT))
        self.assertGreater(os.path.getsize(CKPT), 0)
        import torch
        ckpt = torch.load(CKPT, map_location="cpu")
        for key in ("state_dict", "classes", "input_size"):
            self.assertIn(key, ckpt)
        self.assertIsInstance(ckpt["classes"], list)
        self.assertEqual(len(ckpt["classes"]), len(set(ckpt["classes"])))
        self.assertEqual(int(ckpt["input_size"]), self.model.input_size)
        self.assertEqual(len(ckpt["classes"]), len(self.model.classes))

    def test_output_dims(self):
        # 随机 96x96 BGR 图像，batch 形状 (N, C)，C = 类别数
        crops = [np.random.RandomState(i).randint(0, 256, (96, 96, 3), dtype=np.uint8) for i in range(3)]
        probs = self.model.predict_crops(crops)
        self.assertEqual(probs.shape, (3, len(self.model.classes)))
        self.assertTrue(np.isfinite(probs).all())
        np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-5)
        # 单张也应返回 (1, C)
        single = self.model.predict_crops([crops[0]])
        self.assertEqual(single.shape, (1, len(self.model.classes)))

    def test_same_input_twice_identical(self):
        crop = np.random.RandomState(42).randint(0, 256, (96, 96, 3), dtype=np.uint8)
        a = self.model.predict_crops([crop])
        b = self.model.predict_crops([crop])
        np.testing.assert_allclose(a, b, atol=1e-6)

    def test_module_level_api(self):
        # 模块级 load_model()/predict_crops() 也应可用（默认 checkpoint）
        from clashlab import recog_model as rm
        m = rm.load_model()
        p = rm.predict_crops([np.zeros((96, 96, 3), np.uint8)])
        self.assertEqual(p.shape[1], len(m.classes))


if __name__ == "__main__":
    unittest.main()
