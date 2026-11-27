# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from ultralytics import YOLO
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
data = os.path.join(BASE, "datasets", "detect", "data.yaml")
m = YOLO("yolov8n.pt")
r = m.train(data=data, epochs=20, imgsz=640, batch=8, device=0, workers=0,
            project=os.path.join(BASE, "out", "detect_runs"), name="v1", exist_ok=True, verbose=True)
print("BEST:", r.save_dir)
print(os.path.join(r.save_dir, "weights", "best.pt"))
