# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "out", "overlay", "_p3b", "panel_score_stdout.txt")
b = open(p, "rb").read()
try:
    s = b.decode("utf-8")
except Exception:
    s = b.decode("gbk", "replace")
bad = [l for l in s.splitlines() if any(k in l for k in ("Traceback", "Error", "error", "Exception"))]
print("lines", len(s.splitlines()), "errors", len(bad))
for l in bad[:5]:
    print("", "".join(ch if 32 <= ord(ch) < 127 or ord(ch) > 0x2E80 else " " for ch in l)[:160])
print("tail:")
for l in s.splitlines()[-6:]:
    print(" ", "".join(ch if 32 <= ord(ch) < 127 or ord(ch) > 0x2E80 else " " for ch in l)[:160])
