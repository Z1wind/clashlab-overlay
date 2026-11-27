# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tests", "test_apk_export_dataset.py")
t = open(p, encoding="utf-8").read()
t = t.replace('cv2.imwrite(os.path.join(d, "b01.jpg"), img)',
              'os.makedirs(os.path.join(d, "img"), exist_ok=True)\ncv2.imwrite(os.path.join(d, "img", "b01.jpg"), img)')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("test fixed")
