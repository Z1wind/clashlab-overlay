# -*- coding: utf-8 -*-
"""本地网页标注器：HTTP smoke + 保存落盘测试。"""
import json
import os
import sys
import tempfile
import unittest
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

IMG = os.path.join(ROOT, "out", "live", "enemy_scout_live.png")


class TestAnnotateWeb(unittest.TestCase):
    def test_serve_and_save(self):
        import annotate_web
        if not os.path.exists(IMG):
            self.skipTest("no sample image")
        out = tempfile.mkdtemp()
        httpd = annotate_web.serve(IMG, out, port=18765)
        try:
            base = "http://127.0.0.1:18765"
            html = urllib.request.urlopen(base + "/", timeout=5).read().decode("utf-8")
            self.assertIn("ClashLab", html)
            types = json.loads(urllib.request.urlopen(base + "/types", timeout=5).read().decode("utf-8"))
            self.assertIn("air-defense", types)
            img = urllib.request.urlopen(base + "/image", timeout=5).read()
            self.assertGreater(len(img), 1000)
            payload = {"name": "unit_test", "grid": 44, "quad": [[0,0],[1,0],[1,1],[0,1]],
                       "buildings": [{"type": "air-defense", "tile": [10, 10]}], "walls": []}
            req = urllib.request.Request(base + "/save", data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req, timeout=5).read().decode("utf-8")
            self.assertIn("saved", resp)
            path = os.path.join(out, "unit_test_annotated.json")
            self.assertTrue(os.path.exists(path))
            doc = json.load(open(path, encoding="utf-8"))
            self.assertEqual(doc["buildings"][0]["type"], "air-defense")
        finally:
            httpd.shutdown()


if __name__ == "__main__":
    unittest.main()
