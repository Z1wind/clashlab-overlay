# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v27.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.7.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read(); md5 = hashlib.md5(data).hexdigest()
print("APK", len(data), "md5", md5)
doc = os.path.join(BASE, "docs", "APK_20BASES.md")
t = open(doc, encoding="utf-8").read()
import re
t = re.sub(r"md5 [0-9A-F]{32}", "md5 " + md5.upper(), t)
t = t.replace("APK 8,300,644 bytes md5", "APK " + format(len(data), ",") + " bytes md5")
t = t.replace("- 无头浏览器自测（模拟拖到上边缘 60 次）：before=[0.3,0.3] after=[0.3,-0.6] ok=true",
              "- 真机（1920x864）：拖角到上边缘后 corners_norm[0]=[0.024,-0.6]，MIN_Y=-0.6（自动平移生效）\n- 无头浏览器自测（模拟拖到上边缘 60 次）：before=[0.3,0.3] after=[0.3,-0.6] ok=true")
open(doc, "w", encoding="utf-8", newline="\n").write(t)
print("doc updated")
