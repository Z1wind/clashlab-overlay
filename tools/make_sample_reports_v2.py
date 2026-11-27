# -*- coding: utf-8 -*-
"""打包样例报告 v2：战报 HTML + 既有样例报告 zip 内容。"""
import os, zipfile
sys = __import__("sys"); sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat"
out = BASE + "/out/backup/clashlab_sample_reports_20261127_v2.zip"
old = zipfile.ZipFile(BASE + "/out/backup/clashlab_sample_reports_20261127.zip")
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in old.namelist():
        z.writestr(name, old.read(name))
    rep_dir = BASE + "/out/reports"
    if os.path.isdir(rep_dir):
        for f in sorted(os.listdir(rep_dir)):
            if f.endswith('.html'):
                z.write(os.path.join(rep_dir, f), "reports/" + f)
print("zip:", out, os.path.getsize(out), "bytes")
z2 = zipfile.ZipFile(out)
print("entries:", len(z2.infolist()))
for i in z2.infolist()[:18]: print(" ", i.filename, i.file_size, "bytes")