# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, cv2
img = cv2.imdecode(np.fromfile(r"out\live\_shot_now.png", np.uint8), cv2.IMREAD_COLOR)
crop = img[90:260, 1110:1280]
crop = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
cv2.imencode(".png", crop)[1].tofile(r"out\live\boat_crop2.png")
print("saved", crop.shape)
