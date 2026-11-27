# -*- coding: utf-8 -*-
import hashlib, os, shutil, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
subprocess.run([r"E:\leidian\LDPlayer9\adb.exe","-s","emulator-5554","shell","wm","size","1920x1080"], capture_output=True, timeout=60)
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v26.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.6.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read()
md5 = hashlib.md5(data).hexdigest()
print("FINAL APK", len(data), "md5", md5)
doc = os.path.join(BASE, "docs", "APK_20BASES.md")
t = open(doc, encoding="utf-8").read()
t = t.replace("- 画布四周留出 15% 边距（图片约占屏幕 77%），角点可拖到图片外",
              "- 画布按舞台比例留 6% 边距（图片约 88% 大小），角点可拖到图片外：横向约 11 格、纵向约 2.7 格")
t = t.replace("- 无头浏览器自测：off=163,75 / 图片 1088x500 / 角点 outside=[-0.2,0.5] / ok=true",
              "- 无头浏览器自测：off=326,39 / 图片 1245x572 / 角点 outside=[-0.2,0.5] / ok=true")
import re
t = re.sub(r"- APK 8,300,644 bytes md5 [0-9A-F]+；页面脚本 node --check 通过",
           "- APK 8,300,644 bytes md5 " + md5.upper() + "；页面脚本 node --check 通过", t)
open(doc, "w", encoding="utf-8", newline="\n").write(t)
print("doc updated")
