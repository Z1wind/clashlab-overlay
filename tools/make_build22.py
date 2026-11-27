# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "tools", "build_apk21.py")
t = open(src, encoding="utf-8").read()
t = t.replace("classes21", "classes22").replace("dex21", "dex22").replace("base21", "base22").replace("aligned21", "aligned22")
t = t.replace('"--version-code", "3"', '"--version-code", "4"').replace('"--version-name", "0.2.1"', '"--version-name", "0.2.2"')
t = t.replace("ClashLabAnnotator_v21.apk", "ClashLabAnnotator_v22.apk")
t = t.replace("构建 APK v0.2.1", "构建 APK v0.2.2")
open(os.path.join(BASE, "tools", "build_apk22.py"), "w", encoding="utf-8", newline="\n").write(t)
print("build_apk22 written")
