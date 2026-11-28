# -*- coding: utf-8 -*-
"""分类器升级对比：112@40 与 128@35（6 张好数据）。"""
import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
files = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(1, 9)]
exp = ",".join(files)
def run(size, epochs, out, report):
    cmd = [r"D:\Python313\python.exe", "-u", os.path.join(BASE, "tools", "train_real_aug.py"),
           "--export", exp, "--exclude-bases", "0,1", "--epochs", str(epochs), "--size", str(size),
           "--out", os.path.join(BASE, "models", out), "--report", os.path.join(BASE, "out", report)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = [ln for ln in p.stdout.splitlines() if "CV mean" in ln or "hold" in ln or "saved" in ln]
    print("=== size", size, "epochs", epochs, "exit", p.returncode)
    print("\n".join(tail[-10:]))
run(112, 40, "apk_type_cls_s112e40.pt", "apk_type_report_s112e40.json")
run(128, 35, "apk_type_cls_s128e35.pt", "apk_type_report_s128e35.json")
print("SWEEP DONE")
