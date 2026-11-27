# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "tools", "build_apk22.py")
t = open(src, encoding="utf-8").read()
t = t.replace("classes22", "classes23").replace("dex22", "dex23").replace("base22", "base23").replace("aligned22", "aligned23")
t = t.replace('"--version-code", "4"', '"--version-code", "5"').replace('"--version-name", "0.2.2"', '"--version-name", "0.2.3"')
t = t.replace("ClashLabAnnotator_v22.apk", "ClashLabAnnotator_v23.apk").replace("构建 APK v0.2.2", "构建 APK v0.2.3")
open(os.path.join(BASE, "tools", "build_apk23.py"), "w", encoding="utf-8", newline="\n").write(t)
print("build_apk23 written")
