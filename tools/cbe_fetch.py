# -*- coding: utf-8 -*-
"""下载并解压 clash-blueprint-engine（只读参照），列出关键文件。"""
import os, sys, zipfile, urllib.request, shutil
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p3b")
UP = os.path.join(OUT, "upstream")
os.makedirs(OUT, exist_ok=True)
if os.path.isdir(os.path.join(UP, "clash-blueprint-engine-main")):
    print("already extracted")
else:
    zpath = os.path.join(OUT, "cbe.zip")
    if not os.path.exists(zpath):
        urllib.request.urlretrieve("https://codeload.github.com/koniz-dev/clash-blueprint-engine/zip/refs/heads/main", zpath)
    print("zip bytes", os.path.getsize(zpath))
    with zipfile.ZipFile(zpath) as z:
        z.extractall(UP)
    print("extracted")
root_dir = os.path.join(UP, "clash-blueprint-engine-main")
files = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    for f in filenames:
        p = os.path.join(dirpath, f)
        files.append((os.path.relpath(p, root_dir).replace("\\", "/"), os.path.getsize(p)))
print("total files", len(files), "bytes", sum(s for _, s in files))
key = [f for f in files if any(k in f[0] for k in ("ANALYZER", "SIMULATION", "RULES_ENGINE", "SAVE_FORMAT", "GAME_PACKS"))]
for n, s in key:
    print("DOC", n, s)
data = [f for f in files if f[0].startswith("data/games/clash-of-clans")]
print("data pack files", len(data))
for n, s in data[:40]:
    print("DATA", n, s)
an = [f for f in files if "/analyzer/" in f[0] or "packages/analyzer" in f[0]]
print("analyzer files", len(an))
for n, s in an[:40]:
    print("AN", n, s)
