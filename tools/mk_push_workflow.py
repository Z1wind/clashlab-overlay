# -*- coding: utf-8 -*-
"""基于 API 推送（含 .github 文件），用于测试 workflow scope 权限。"""
import json, os, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "tools", "push_changes.py")
t = open(src, encoding="utf-8").read()
t = t.replace('if x and not x.startswith(b".github/workflows/")', 'if x')
t = t.replace('CACHE = os.path.join(BASE, "out", "release", "blob_cache.json")',
              'CACHE = os.path.join(BASE, "out", "release", "blob_cache_wf.json")')
out = os.path.join(BASE, "tools", "push_workflow.py")
open(out, "w", encoding="utf-8", newline="\n").write(t)
print("push_workflow.py written")
