# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "java", "com", "clashlab", "annotator", "MainActivity.java")
t = open(p, encoding="utf-8").read()
t = t.replace('web.loadUrl("file:///android_asset/annotate8.html");', 'web.loadUrl("file:///android_asset/annotate9.html");')
open(p, "w", encoding="utf-8", newline="\n").write(t)
src = os.path.join(BASE, "tools", "build_apk28.py")
b = open(src, encoding="utf-8").read()
b = (b.replace("classes28","classes29").replace("dex28","dex29").replace("base28","base29").replace("aligned28","aligned29")
      .replace('"--version-code", "10"','"--version-code", "11"').replace('"--version-name", "0.2.8"','"--version-name", "0.2.9"')
      .replace("ClashLabAnnotator_v28.apk","ClashLabAnnotator_v29.apk").replace("构建 APK v0.2.8","构建 APK v0.2.9"))
open(os.path.join(BASE, "tools", "build_apk29.py"), "w", encoding="utf-8", newline="\n").write(b)
print("build_apk29 written")
