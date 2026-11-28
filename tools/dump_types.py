# -*- coding: utf-8 -*-
"""保存类型表 json（ONNX 推理需要）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import torch
ck = torch.load(os.path.join(BASE, "models", "pipeline_type.pt"), map_location="cpu")
json.dump({"types": ck["types"], "size": ck.get("size", 96)}, open(os.path.join(BASE, "models", "pipeline_types.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("types", len(ck["types"]), "saved")
