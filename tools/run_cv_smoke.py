# -*- coding: utf-8 -*-
import subprocess, sys, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
files = [os.path.join(BASE, "out", "apk_qa", "cv_exports", n) for n in
         ("b01.json","b02.json","b03.json","b04.json","b05.json")]
p = subprocess.run([r"D:\Python313\python.exe", "-u", os.path.join(BASE, "tools", "train_from_apk_export.py"),
                    "--export", ",".join(files), "--epochs", "8",
                    "--out", os.path.join(BASE, "models", "apk_type_cls_cv.pt"),
                    "--report", os.path.join(BASE, "out", "apk_type_report_cv.json")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(p.stdout[-3000:])
print(p.stderr[-800:])
