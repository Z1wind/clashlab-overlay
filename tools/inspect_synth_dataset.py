# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
d = os.path.join(BASE, "datasets", "synth_level")
print("files:", os.listdir(d))
imgs = np.load(os.path.join(d, "imgs.npy"), mmap_mode="r")
print("imgs:", imgs.shape, imgs.dtype)
lab = json.load(open(os.path.join(d, "labels.json"), encoding="utf-8"))
print("labels:", len(lab), "sample:", lab[0])
print("types:", len({l["type"] for l in lab}))
