# -*- coding: utf-8 -*-
"""打开源包：按 .gitignore 规则挑源文件 → zip；同时把 exe 复制到 release 目录并生成 SHA256SUMS。"""
import os, sys, zipfile, hashlib, fnmatch

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
REL = os.path.join(BASE, "out", "release")
os.makedirs(REL, exist_ok=True)
VERSION = "v0.1.0"
zip_path = os.path.join(REL, "ClashLab_open_source_%s.zip" % VERSION)

# tools/ 是开发期实验脚本（含本机绝对路径与大量实验产物），不随开源包发布
INCLUDE_DIRS = ["clashlab", "tests", "bases", "assets", "config", "docs", "layouts"]
INCLUDE_FILES = ["README.md", "README.en.md", "LICENSE", "ATTRIBUTIONS.md", "PACKAGING.md",
                 "CONTRIBUTING.md", "CHANGELOG.md", "SECURITY.md",
                 "requirements.txt", "requirements-dev.txt",
                 ".gitignore", "run_overlay.py", "overlay_exe_main.py", "build_overlay.ps1",
                 "ClashOverlay.spec"]  # 打开标注工具.cmd 含本机绝对路径，不入包
EXCLUDE_DIR_PARTS = {"out", "dist", "build", "__pycache__", ".git", ".dsh", ".vscode", ".idea"}
EXCLUDE_SUFFIX = (".pyc", ".pyo", ".bak", ".tmp")
EXCLUDE_PREFIX = ("项目导出_",)


TOOLS_KEEP_EXT = (".py", ".ps1", ".cmd", ".bat", ".md", ".txt")


def keep_file(rel_path):
    parts = rel_path.split("/")
    # tools/ 只收脚本与说明，排除实验产物（png/json/npz/pt/csv/log/bin 等约 180MB）
    if parts[0] == "tools":
        return parts[-1].lower().endswith(TOOLS_KEEP_EXT)
    if any(p in EXCLUDE_DIR_PARTS for p in parts[:-1]):
        return False
    name = parts[-1]
    if unsigned(name).startswith(EXCLUDE_PREFIX):
        return False
    if any(s in name for s in ("__pycache__",)):
        return False
    if name.endswith(EXCLUDE_SUFFIX):
        return False
    if ".bak_" in name or name.endswith(".bak"):
        return False
    if name == "_probe_template.py":  # 素材探针脚本含本机 ROOT 绝对路径，不入包
        return False
    return True


def unsigned(s):
    return s


def walk_files():
    for f in INCLUDE_FILES:
        p = os.path.join(BASE, f)
        if os.path.isfile(p):
            yield f, p
    for d in INCLUDE_DIRS:
        root = os.path.join(BASE, d)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [x for x in dirnames if x not in EXCLUDE_DIR_PARTS]
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, BASE).replace("\\", "/")
                if keep_file(rel):
                    yield rel, p


TEXT_EXT = (".py", ".md", ".txt", ".json", ".ps1", ".cmd", ".spec", ".gitignore")
PLACEHOLDER = "<repo-root>"


def sanitize(data):
    """把本机绝对路径替换成占位符，避免用户名/目录结构泄露。"""
    s = data.decode("utf-8", "ignore")
    s = s.replace(BASE, PLACEHOLDER).replace(BASE.replace("\\", "/"), PLACEHOLDER)
    return s.encode("utf-8")


items = list(walk_files())
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for rel, p in items:
        if rel.endswith(TEXT_EXT):
            z.writestr(rel, sanitize(open(p, "rb").read()))
        else:
            z.write(p, rel)
print("zip", zip_path, os.path.getsize(zip_path), "B, files", len(items))
# 统计各类
kinds = {}
for rel, _ in items:
    top = rel.split("/")[0] if "/" in rel else "(root)"
    kinds[top] = kinds.get(top, 0) + 1
print("top-level:", kinds)

# exe + SHA256SUMS
import shutil
exe_src = os.path.join(BASE, "dist", "ClashOverlay.exe")
exe_dst = os.path.join(REL, "ClashOverlay.exe")
if os.path.exists(exe_src):
    shutil.copy2(exe_src, exe_dst)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


lines = []
for f in ("ClashLab_open_source_%s.zip" % VERSION, "ClashOverlay.exe"):
    p = os.path.join(REL, f)
    if os.path.exists(p):
        lines.append("%s  %s  %d B" % (sha256(p), f, os.path.getsize(p)))
open(os.path.join(REL, "SHA256SUMS.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("SHA256SUMS:")
for l in lines:
    print(" ", l)
