# -*- coding: utf-8 -*-
"""热键流水线端到端：伪造 rt（_default_grab 返回截图）触发 _start_ocr_job，检查落盘。"""
import json, os, sys, tempfile, time
import numpy as np, cv2
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab.overlay import runtime

root = tempfile.mkdtemp()
img = cv2.imdecode(np.fromfile(r"out\ocr_test.png", np.uint8), cv2.IMREAD_COLOR)

class RT:
    def __init__(self, root):
        self.root = root
    def _default_grab(self):
        return img
    def log(self, msg):
        print("[log]", msg, flush=True)

rt = RT(root)
runtime._start_ocr_job(rt)
path = os.path.join(root, "out", "ocr_latest.json")
deadline = time.time() + 45
while time.time() < deadline and not os.path.exists(path):
    time.sleep(0.5)
print("latest exists:", os.path.exists(path))
if os.path.exists(path):
    d = json.load(open(path, encoding="utf-8"))
    print("TH:", d.get("th"), "| line:", d.get("line"))
    print("player:", (d.get("api") or {}).get("player"))
