# -*- coding: utf-8 -*-
"""发布包完整性核验 v2：清单 / 必备 / 排除 / 密钥 / 绝对路径（按目录分组）。"""
import os, zipfile, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
zp = os.path.join(BASE, "out", "release", "ClashLab_open_source_v0.1.0.zip")
z = zipfile.ZipFile(zp)
names = z.namelist()
print("entries:", len(names), "zip bytes:", os.path.getsize(zp))
bad = [n for n in names if n.split("/")[0] in ("out", "dist", "build") or "__pycache__" in n or n.endswith((".pyc", ".bak")) or n.startswith("tools/")]
print("违规/不该入包:", len(bad), bad[:5])
sk = {}
abs_path = {}
for n in names:
    if not n.endswith((".py", ".md", ".txt", ".json", ".ps1", ".cmd", ".spec")):
        continue
    try:
        s = z.read(n).decode("utf-8", "ignore")
    except Exception:
        continue
    top = n.split("/")[0] if "/" in n else "(root)"
    if re.search(r"sk-[A-Za-z0-9]{12,}", s) and "redacted" not in s:
        sk[top] = sk.get(top, 0) + 1
    if "C:\\\\Users\\\\" in s or "C:/Users/" in s:
        abs_path[top] = abs_path.get(top, 0) + 1
print("sk- 命中:", sk or 0)
print("绝对路径命中:", abs_path or 0)
must = ["README.md", "LICENSE", "PACKAGING.md", "requirements.txt", "run_overlay.py",
        "clashlab/overlay/runtime.py", "clashlab/overlay/sim_panel.py", "clashlab/overlay/giant_arrow_diagram.py",
        "clashlab/layout_score.py", "tests/test_layout_score.py", "docs/教程.md",
        "bases/th16/03/layout.json", "assets/coc"]
print("必备:", sum(1 for m in must if (m in names) or any(n.startswith(m.rstrip("/") + "/") for n in names)), "/", len(must))
