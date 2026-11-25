# -*- coding: utf-8 -*-
"""发布包完整性核验：清单、必备文件、目录排除、密钥/绝对路径扫描。"""
import os, zipfile, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
zp = os.path.join(BASE, "out", "release", "ClashLab_open_source_v0.1.0.zip")
z = zipfile.ZipFile(zp)
names = z.namelist()
print("entries:", len(names), "zip bytes:", os.path.getsize(zp))
bad_dirs = [n for n in names if n.split("/")[0] in ("out", "dist", "build") or "__pycache__" in n or n.endswith((".pyc", ".bak"))]
print("排除项违规:", len(bad_dirs), bad_dirs[:5])
must = ["README.md", "LICENSE", "PACKAGING.md", "requirements.txt", "run_overlay.py",
        "clashlab/overlay/runtime.py", "clashlab/layout_score.py", "tests/test_layout_score.py",
        "docs/教程.md", "bases/th16/03/layout.json", "assets/coc"]
for m in must:
    hit = any(n == m or n.startswith(m.rstrip("/") + "/") or m in n for n in names)
    print(("OK  " if hit else "MISS"), m)
sk_hits, path_hits = 0, 0
for n in names:
    if not n.endswith((".py", ".md", ".txt", ".json", ".ps1", ".cmd", ".spec")):
        continue
    try:
        s = z.read(n).decode("utf-8", "ignore")
    except Exception:
        continue
    if re.search(r"sk-[A-Za-z0-9]{12,}", s) and "redacted" not in s:
        sk_hits += 1
    if "C:\\Users\\" in s:
        path_hits += 1
print("包内 sk- 明文文件数:", sk_hits, " 含 C:\\Users\\ 的文件数:", path_hits)
# 抽样列目录
print("root files:", sorted([n for n in names if "/" not in n]))
