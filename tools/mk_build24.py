# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "tools", "build_apk23.py")
t = open(src, encoding="utf-8").read()
t = (t.replace("classes23", "classes24").replace("dex23", "dex24")
      .replace("base23", "base24").replace("aligned23", "aligned24")
      .replace('"--version-code", "5"', '"--version-code", "6"')
      .replace('"--version-name", "0.2.3"', '"--version-name", "0.2.4"')
      .replace("ClashLabAnnotator_v23.apk", "ClashLabAnnotator_v24.apk")
      .replace("构建 APK v0.2.3", "构建 APK v0.2.4"))
open(os.path.join(BASE, "tools", "build_apk24.py"), "w", encoding="utf-8", newline="\n").write(t)
print("build_apk24 written")
