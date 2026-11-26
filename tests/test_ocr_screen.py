# -*- coding: utf-8 -*-
"""OCR 解析纯函数测试（不需要 OCR 引擎）。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOcrParse(unittest.TestCase):
    def test_basic_wall_screenshot(self):
        from clashlab.ocr_screen import _parse_lines
        got = _parse_lines(["15.", "MH Tipu", "baby warrior"])
        self.assertTrue(str(got["level"]).startswith("15"))
        self.assertEqual(got["name"], "MH Tipu")
        self.assertEqual(got["clan"], "baby warrior")

    def test_with_badge_ignored(self):
        from clashlab.ocr_screen import _parse_lines
        got = _parse_lines([{"text": "205", "score": 0.9}, {"text": "15.", "score": 0.9},
                            {"text": "MH Tipu", "score": 0.9}, {"text": "baby warrior", "score": 0.9}])
        self.assertEqual(got["name"], "MH Tipu")
        self.assertEqual(got["clan"], "baby warrior")

    def test_only_name(self):
        from clashlab.ocr_screen import _parse_lines
        got = _parse_lines(["17.", "LongName With Spaces"])
        self.assertEqual(got["name"], "LongName With Spaces")
        self.assertIsNone(got["clan"])

    def test_empty(self):
        from clashlab.ocr_screen import _parse_lines
        self.assertEqual(_parse_lines([]), {"level": None, "name": None, "clan": None})


if __name__ == "__main__":
    unittest.main()
