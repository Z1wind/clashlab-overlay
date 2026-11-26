# -*- coding: utf-8 -*-
"""解压 JDK + cmdline-tools 到 E:\tools（避开 C 盘）。"""
import os, shutil, zipfile

SETUP = r"E:\tools\android-setup"
TOOLS = r"E:\tools"
JDK_DIR = os.path.join(TOOLS, "jdk17")
SDK_DIR = os.path.join(TOOLS, "android-sdk")

def extract(zip_path, dest):
    if os.path.isdir(dest) and os.listdir(dest):
        print("[skip] already exists:", dest); return
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)
    print("[extracted]", zip_path, "->", dest)

# JDK：zip 内是 jdk-17.../ 一层
if not os.path.isdir(JDK_DIR) or not os.listdir(JDK_DIR):
    tmp = os.path.join(TOOLS, "_jdk_tmp")
    extract(os.path.join(SETUP, "jdk17.zip"), tmp)
    inner = [d for d in os.listdir(tmp) if os.path.isdir(os.path.join(tmp, d))]
    src = os.path.join(tmp, inner[0]) if inner else tmp
    if os.path.isdir(JDK_DIR):
        shutil.rmtree(JDK_DIR, ignore_errors=True)
    shutil.move(src, JDK_DIR)
    shutil.rmtree(tmp, ignore_errors=True)
    print("[jdk] ->", JDK_DIR, os.listdir(JDK_DIR)[:5])

# cmdline-tools：期望 android-sdk/cmdline-tools/latest/bin
if not os.path.isdir(os.path.join(SDK_DIR, "cmdline-tools", "latest", "bin")):
    tmp = os.path.join(SDK_DIR, "_ct")
    extract(os.path.join(SETUP, "cmdline-tools.zip"), tmp)
    src = os.path.join(tmp, "cmdline-tools")
    dst = os.path.join(SDK_DIR, "cmdline-tools", "latest")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(dst):
        shutil.rmtree(dst, ignore_errors=True)
    shutil.move(src, dst)
    shutil.rmtree(tmp, ignore_errors=True)
    print("[cmdline-tools] ->", dst)
print("EXTRACT_DONE")
