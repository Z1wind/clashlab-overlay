# -*- coding: utf-8 -*-
"""检查仓库内 markdown 的相对链接/图片是否存在（外链只统计不请求）。"""
import os, re, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
md_files = []
for dirpath, dirnames, filenames in os.walk(BASE):
    dirnames[:] = [d for d in dirnames if d not in {".git", "out", "dist", "build", "build_v7", "build_v8",
                                                    "build_v9", "build_v7b", "build_v7c", "build_v7d",
                                                    "scripts", "_archive", "dataset", "__pycache__"}]
    for fn in filenames:
        if fn.endswith(".md"):
            md_files.append(os.path.join(dirpath, fn))
link_re = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
missing, external, total = [], 0, 0
for p in md_files:
    rel_dir = os.path.dirname(p)
    txt = open(p, encoding="utf-8", errors="replace").read()
    for m in link_re.finditer(txt):
        url = m.group(1).strip()
        if url.startswith(("http://", "https://", "mailto:", "#")):
            external += 1
            continue
        target = url.split("#")[0].strip()
        if not target:
            continue
        total += 1
        cand = os.path.normpath(os.path.join(rel_dir, target))
        if not os.path.exists(cand):
            missing.append((os.path.relpath(p, BASE), url))
print("markdown files:", len(md_files), "| relative links:", total, "| external:", external)
print("missing:", len(missing))
for p, u in missing:
    print("  ", p, "->", u)
