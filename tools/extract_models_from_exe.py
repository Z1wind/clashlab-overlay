# -*- coding: utf-8 -*-
"""从 PyInstaller onefile EXE 中提取 models/*.onnx 并验证。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
exe = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v1.7.exe")
from PyInstaller.archive.readers import CArchiveReader
arch = CArchiveReader(exe)
names = [n for n in arch.toc if "hybrid" in n or "img/" in n]
print("archive entries:", len(arch.toc), "| hybrid/img:", len(names))
for n in names: print(" ", n)
outdir = os.path.join(BASE, "models_good_v17")
os.makedirs(outdir, exist_ok=True)
for n in names:
    if n.startswith("models"):
        data = arch.extract(n)
        dst = os.path.join(outdir, os.path.basename(n))
        open(dst, "wb").write(data)
        print("extracted", os.path.basename(n), len(data))
