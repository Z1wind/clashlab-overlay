# -*- coding: utf-8 -*-
import hashlib, os, shutil, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
subprocess.run([r"E:\leidian\LDPlayer9\adb.exe","-s","emulator-5554","shell","wm","size","1920x1080"], capture_output=True, timeout=60)
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v25.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.5.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read()
print("FINAL APK", len(data), "bytes md5", hashlib.md5(data).hexdigest())
doc = os.path.join(BASE, "docs", "APK_20BASES.md")
t = open(doc, encoding="utf-8").read()
old = "- 构建：ClashLabAnnotator_v25.apk 8,292,385 bytes md5 C68032E0DB48772ED175DABDA78D8D3A"
new = "- 构建：ClashLabAnnotator_v25.apk 8,292,385 bytes md5 " + hashlib.md5(data).hexdigest().upper() + "（帮助文案/双击提示已更新）"
t = t.replace(old, new)
open(doc, "w", encoding="utf-8", newline="\n").write(t)
print("doc md5 updated")
