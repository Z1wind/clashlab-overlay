# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import torch, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ck = torch.load(os.path.join(BASE, "models", "synth_level.pt"), map_location="cpu", weights_only=False)
print("ckpt keys:", list(ck.keys()))
for k, v in ck.items():
    if k == "state_dict":
        print("state_dict params:", len(v))
    elif isinstance(v, (list, tuple)):
        print(k, "len", len(v), "sample", v[:5])
    else:
        print(k, type(v), v if not hasattr(v, "shape") else v.shape)
