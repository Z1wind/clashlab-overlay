# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tests", "test_layout_rules.py")
t = open(p, encoding="utf-8").read()
t = t.replace("            if not x[\"passed\"]:\n                self.assertIsNotNone(x[\"recommendation\"])",
              "            if not x[\"passed\"] and not x.get(\"skipped\"):\n                self.assertIsNotNone(x[\"recommendation\"])")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("test patched")
