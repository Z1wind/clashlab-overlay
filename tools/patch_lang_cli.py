# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

# run_overlay --lang
p = os.path.join(BASE, "run_overlay.py")
t = open(p, encoding="utf-8").read()
if "--lang" not in t:
    t = t.replace('    ap.add_argument("--allow-primary"', '    ap.add_argument("--lang", default=None, choices=["auto", "zh", "en"],\n'
                    '                    help="UI language: auto / zh / en (overrides config/ui.json)")\n'
                    '    ap.add_argument("--allow-primary"', 1)
    t = t.replace("    a = ap.parse_args()", '    a = ap.parse_args()\n    if getattr(a, "lang", None):\n        os.environ["CLASHLAB_LANG"] = a.lang', 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("run_overlay --lang added")

# exe shim --lang
p2 = os.path.join(BASE, "overlay_exe_main.py")
t2 = open(p2, encoding="utf-8").read()
if "--lang" not in t2:
    t2 = t2.replace('    ap.add_argument("--allow-primary", action="store_true",',
                    '    ap.add_argument("--lang", default=None, choices=["auto", "zh", "en"],\n'
                    '                    help="UI language: auto / zh / en")\n'
                    '    ap.add_argument("--allow-primary", action="store_true",', 1)
    t2 = t2.replace("    a = ap.parse_args()", '    a = ap.parse_args()\n    if getattr(a, "lang", None):\n        import os as _os\n        _os.environ["CLASHLAB_LANG"] = a.lang', 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("exe --lang added")

# 测试
test = '''# -*- coding: utf-8 -*-
"""中英文切换测试：config 持久化、环境变量覆盖、_L 文案。"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class TestLang(unittest.TestCase):
    def setUp(self):
        os.environ.pop("CLASHLAB_LANG", None)
        from clashlab.overlay import lang
        lang._loaded_root = None
        lang._current = "auto"
        self.lang = lang

    def test_default_auto(self):
        root = tempfile.mkdtemp()
        self.assertEqual(self.lang.ensure_loaded(root), "auto")

    def test_set_persists_and_reload(self):
        root = tempfile.mkdtemp()
        self.lang.set(root, "en")
        doc = json.load(open(os.path.join(root, "config", "ui.json"), encoding="utf-8"))
        self.assertEqual(doc["lang"], "en")
        self.lang._loaded_root = None
        self.assertEqual(self.lang.ensure_loaded(root), "en")

    def test_env_override(self):
        root = tempfile.mkdtemp()
        self.lang.set(root, "zh")
        os.environ["CLASHLAB_LANG"] = "en"
        self.lang._loaded_root = None
        self.assertEqual(self.lang.ensure_loaded(root), "en")

    def test_label(self):
        self.lang._current = "en"
        self.assertEqual(self.lang.label("研究", "Research"), "Research")
        self.lang._current = "zh"
        self.assertEqual(self.lang.label("研究", "Research"), "研究")

    def test_invalid_mode(self):
        root = tempfile.mkdtemp()
        with self.assertRaises(ValueError):
            self.lang.set(root, "fr")

    def test_pages_L_respects_mode(self):
        from clashlab.overlay import pages, lang
        lang._current = "en"
        self.assertEqual(pages._L(True, "设置", "setting"), "setting")
        lang._current = "zh"
        self.assertEqual(pages._L(False, "设置", "setting"), "设置")
        lang._current = "auto"
        self.assertEqual(pages._L(False, "设置", "setting"), "setting")


if __name__ == "__main__":
    unittest.main()
'''
pp = os.path.join(BASE, "tests", "test_lang.py")
open(pp, "w", encoding="utf-8", newline="\n").write(test)
print("tests written")
