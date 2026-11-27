# -*- coding: utf-8 -*-
import os, tempfile, unittest, urllib.request
from PIL import Image
from clashlab import annotator

PORT = 8911

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = tempfile.mkdtemp()
        cls.img = os.path.join(d, "t.png")
        Image.new("RGB", (64, 48), (40, 80, 40)).save(cls.img)
        cls.root = d

    def test_1_start_and_http(self):
        annotator.stop_server()
        h = annotator.start_server(self.root, image=self.img, port=PORT)
        self.assertIsNotNone(h)
        self.assertTrue(annotator.is_running(PORT))
        with urllib.request.urlopen("http://127.0.0.1:%d/" % PORT, timeout=5) as r:
            body = r.read().decode("utf-8", "ignore")
        self.assertEqual(r.status, 200)
        self.assertIn("ClashLab annotator", body)

    def test_2_idempotent(self):
        h = annotator.start_server(self.root, image=self.img, port=PORT)
        self.assertIsNone(h)          # 已在跑 -> 不重复启动
        self.assertTrue(annotator.is_running(PORT))

    def test_3_stop(self):
        annotator.stop_server()
        import time
        for _ in range(20):
            if not annotator.is_running(PORT):
                break
            time.sleep(0.1)
        self.assertFalse(annotator.is_running(PORT))

    def test_4_missing_image(self):
        annotator.stop_server()
        with self.assertRaises(FileNotFoundError):
            annotator.start_server(self.root, image=os.path.join(self.root, "nope.png"), port=PORT)

if __name__ == "__main__":
    unittest.main()
