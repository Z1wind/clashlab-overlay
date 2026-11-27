# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "java", "com", "clashlab", "annotator", "MainActivity.java")
t = open(p, encoding="utf-8").read()
t = t.replace('web.loadUrl("file:///android_asset/annotate7.html");', 'web.loadUrl("file:///android_asset/annotate8.html");')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("activity -> annotate8")
src = os.path.join(BASE, "tools", "build_apk27.py")
b = open(src, encoding="utf-8").read()
b = (b.replace("classes27","classes28").replace("dex27","dex28").replace("base27","base28").replace("aligned27","aligned28")
      .replace('"--version-code", "9"','"--version-code", "10"').replace('"--version-name", "0.2.7"','"--version-name", "0.2.8"')
      .replace("ClashLabAnnotator_v27.apk","ClashLabAnnotator_v28.apk").replace("构建 APK v0.2.7","构建 APK v0.2.8"))
open(os.path.join(BASE, "tools", "build_apk28.py"), "w", encoding="utf-8", newline="\n").write(b)
print("build_apk28 written")
