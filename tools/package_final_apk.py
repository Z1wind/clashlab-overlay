# -*- coding: utf-8 -*-
import json, os, shutil, subprocess, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"
QA = os.path.join(BASE, "out", "apk_qa")
# 1) 拉取并校验 JSON
subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/Download/annot_b01.json",
                os.path.join(QA, "final_annot_b01.json")], capture_output=True, text=True)
p = os.path.join(QA, "final_annot_b01.json")
d = json.load(open(p, encoding="utf-8"))
print("json keys:", sorted(d.keys()))
print("image:", d.get("image"), "| corners:", len(d.get("corners") or []),
      "| buildings:", len(d.get("buildings") or []), "| tile:", (d.get("buildings") or [{}])[0].get("tile"))
# 2) 拷贝最终 APK 到项目 dist
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v20.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.0.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read()
print("FINAL_APK", os.path.basename(dst), len(data), "bytes md5", hashlib.md5(data).hexdigest())
