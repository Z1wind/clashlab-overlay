# -*- coding: utf-8 -*-
# 抓帧存 ladder（exec-out 解码，绕开 adb pull 中文路径问题）；用法 grab.py <outname>
import subprocess, sys, cv2, numpy as np, os
ADB=r"E:\leidian\LDPlayer9\adb.exe"
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
name=sys.argv[1]
raw=subprocess.run([ADB,"exec-out","screencap","-p"],capture_output=True,timeout=30).stdout
img=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
cv2.imencode(".png",img)[1].tofile(os.path.join(D,name))
print("saved",name,img.shape)
