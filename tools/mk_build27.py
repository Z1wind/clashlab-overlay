# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
st = os.path.join(BASE, "android", "assets", "annotate7_selftest.html")
if os.path.exists(st): os.remove(st); print("selftest removed")
p = os.path.join(BASE, "android", "assets", "annotate7.html")
t = open(p, encoding="utf-8").read()
t = t.replace("<h3>30 秒上手（v0.2.6）</h3>", "<h3>30 秒上手（v0.2.7）</h3>")
t = t.replace("黄点出现后<b>按住可拖动</b>到真正的角，<b>可以拖到图片外面</b>（截图被裁掉边缘时用）。",
              "黄点出现后<b>按住可拖动</b>到真正的角，可拖到图片外面；拖到屏幕边缘会<b>自动平移</b>。")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("help updated v0.2.7")
src = os.path.join(BASE, "tools", "build_apk26.py")
b = open(src, encoding="utf-8").read()
b = (b.replace("classes26","classes27").replace("dex26","dex27").replace("base26","base27").replace("aligned26","aligned27")
      .replace('"--version-code", "8"','"--version-code", "9"').replace('"--version-name", "0.2.6"','"--version-name", "0.2.7"')
      .replace("ClashLabAnnotator_v26.apk","ClashLabAnnotator_v27.apk").replace("构建 APK v0.2.6","构建 APK v0.2.7"))
open(os.path.join(BASE, "tools", "build_apk27.py"), "w", encoding="utf-8", newline="\n").write(b)
print("build_apk27 written")
