# -*- coding: utf-8 -*-
"""从构建日志里抽错误行（去掉控制字符/非 ASCII），写成干净文本。"""
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p2d")
raw = open(os.path.join(OUT, "build_log.txt"), "rb").read().decode("utf-8", "replace")
clean = []
for line in raw.splitlines():
    l = "".join(ch if 32 <= ord(ch) < 127 or ch in "\t" else " " for ch in line).strip()
    if not l:
        continue
    if re.search(r"error|Error|ERROR|Traceback|PyInstaller|Exception|Fatal|failed|FAILED|ModuleNotFound|No such|not found|BUILD", l):
        clean.append(l)
open(os.path.join(OUT, "build_errors.txt"), "w", encoding="utf-8").write("\n".join(clean[-60:]))
print("clean_lines", len(clean))
