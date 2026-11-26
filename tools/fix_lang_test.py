# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tests", "test_lang.py")
t = open(p, encoding="utf-8").read()
if "def tearDown" not in t:
    t = t.replace('''    def test_default_auto(self):''',
'''    def tearDown(self):
        # 测试会改全局语言状态；复位，避免污染其它测试模块（曾导致面板测试误判为英文）
        os.environ.pop("CLASHLAB_LANG", None)
        self.lang._loaded_root = None
        self.lang._current = "auto"

    def test_default_auto(self):''', 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("tearDown added")
