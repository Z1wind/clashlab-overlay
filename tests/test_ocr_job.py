# -*- coding: utf-8 -*-
"""ocr_job 流水线测试（不联网、不真 OCR）。"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOcrJob(unittest.TestCase):
    def test_format_line_with_player(self):
        from clashlab import ocr_job
        line = ocr_job.format_line({"name": "Mh Tipu"}, {"player": {"name": "MH Tipu", "tag": "#X", "th": 15}}, 15)
        self.assertIn("MH Tipu", line)
        self.assertIn("TH15", line)
        self.assertIn("OCR+API", line)

    def test_format_line_ocr_only(self):
        from clashlab import ocr_job
        line = ocr_job.format_line({"name": "Mh Tipu", "level": "16."}, None, None)
        self.assertIn("TH16", line)
        self.assertIn("OCR", line)

    def test_save_load_roundtrip(self):
        from clashlab import ocr_job
        root = tempfile.mkdtemp()
        payload = {"ocr": {"name": "x"}, "th": 15, "line": "l"}
        p = ocr_job.save(root, payload)
        self.assertTrue(os.path.exists(p))
        self.assertEqual(ocr_job.load(root)["th"], 15)

    def test_apply_to_layout(self):
        from clashlab import ocr_job
        lay = {"buildings": [{"type": "cannon", "tile": [3, 3]}, {"type": "ghost-tower", "tile": [4, 4]}]}
        out, n = ocr_job.apply_to_layout(lay, {"th": 16})
        self.assertGreaterEqual(n, 1)
        self.assertNotIn("level", lay["buildings"][0])  # 原对象不被改
        self.assertGreaterEqual(out["buildings"][0]["level"], 1)

    def test_run_ocr_monkeypatched(self):
        from clashlab import ocr_job, ocr_screen, cocapi
        root = tempfile.mkdtemp()
        orig_read, orig_resolve = ocr_screen.read_opponent, cocapi.resolve_opponent
        try:
            ocr_screen.read_opponent = lambda img: {"level": "16.", "name": "Mh Tipu", "clan": "baby w", "lines": []}
            cocapi.resolve_opponent = lambda *a, **kw: {"player": {"name": "MH Tipu", "tag": "#X", "th": 15}}
            payload = ocr_job.run_ocr(root, object())
        finally:
            ocr_screen.read_opponent, cocapi.resolve_opponent = orig_read, orig_resolve
        self.assertEqual(payload["th"], 15)
        self.assertIn("MH Tipu", payload["line"])
        self.assertTrue(os.path.exists(ocr_job.latest_path(root)))


if __name__ == "__main__":
    unittest.main()
