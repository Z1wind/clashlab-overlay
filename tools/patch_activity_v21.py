# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "java", "com", "clashlab", "annotator", "MainActivity.java")
t = open(p, encoding="utf-8").read()
t = t.replace('web.loadUrl("file:///android_asset/annotate2.html");', 'web.loadUrl("file:///android_asset/annotate3.html");')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("MainActivity -> annotate3.html")
