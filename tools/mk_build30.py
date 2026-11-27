# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "java", "com", "clashlab", "annotator", "MainActivity.java")
t = open(p, encoding="utf-8").read()
t = t.replace('web.loadUrl("file:///android_asset/annotate9.html");', 'web.loadUrl("file:///android_asset/annotate10.html");')
open(p, "w", encoding="utf-8", newline="\n").write(t)
src = os.path.join(BASE, "tools", "build_apk29.py")
b = open(src, encoding="utf-8").read()
b = (b.replace("classes29","classes30").replace("dex29","dex30").replace("base29","base30").replace("aligned29","aligned30")
      .replace('"--version-code", "11"','"--version-code", "12"').replace('"--version-name", "0.2.9"','"--version-name", "0.3.0"')
      .replace("ClashLabAnnotator_v29.apk","ClashLabAnnotator_v30.apk").replace("构建 APK v0.2.9","构建 APK v0.3.0"))
open(os.path.join(BASE, "tools", "build_apk30.py"), "w", encoding="utf-8", newline="\n").write(b)
print("build_apk30 written")
