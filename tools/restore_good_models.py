# -*- coding: utf-8 -*-
import os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
models = os.path.join(BASE, "models")
bad = os.path.join(BASE, "models_bad_retrain")
os.makedirs(bad, exist_ok=True)
for f in ("hybrid_gate.onnx","hybrid_emb.onnx","hybrid_protos.npz","hybrid_meta.json",
          "hybrid_gate.pt","hybrid_emb.pt"):
    src = os.path.join(models, f)
    if os.path.exists(src): shutil.copyfile(src, os.path.join(bad, f))
print("backed up current models ->", bad)
good = os.path.join(BASE, "models_good_v17")
for f in os.listdir(good):
    shutil.copyfile(os.path.join(good, f), os.path.join(models, f))
print("restored good v1.7 models")
# 推理恢复为与好模型一致的约定（_crop(cx,cy)，中心 cx+0.5）
q = os.path.join(BASE, "tools", "preannotate_core.py")
s = open(q, encoding="utf-8").read()
s = s.replace("_crop(img, cal, cx + .5, cy + .5, self.size)", "_crop(img, cal, cx, cy, self.size)")
open(q, "w", encoding="utf-8", newline="\n").write(s)
print("inference convention restored; remaining centered:", s.count("cx + .5, cy + .5"))
