# -*- coding: utf-8 -*-
"""从 .pt 导出 ONNX 并用 onnxruntime 校验。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import numpy as np, torch, torch.nn as nn
S = 96
class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.25); self.head = nn.Linear(192, n)
    def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
def load(pt, kind):
    ck = torch.load(pt, map_location="cpu")
    n = 2 if kind == "gate" else len(ck["types"])
    net = Net(n); net.load_state_dict(ck["model"]); net.eval()
    return net, ck
gate, _ = load(os.path.join(BASE,"models","pipeline_gate.pt"), "gate")
tnet, ck = load(os.path.join(BASE,"models","pipeline_type.pt"), "type")
dummy = torch.randn(1,3,S,S)
torch.onnx.export(gate, dummy, os.path.join(BASE,"models","pipeline_gate.onnx"),
                  input_names=["input"], output_names=["logits"], opset_version=18, dynamo=False)
torch.onnx.export(tnet, dummy, os.path.join(BASE,"models","pipeline_type.onnx"),
                  input_names=["input"], output_names=["logits"], opset_version=18, dynamo=False)
print("exported onnx")
import onnxruntime as ort
x = np.random.rand(1,3,S,S).astype(np.float32)
sg = ort.InferenceSession(os.path.join(BASE,"models","pipeline_gate.onnx"), providers=["CPUExecutionProvider"])
st = ort.InferenceSession(os.path.join(BASE,"models","pipeline_type.onnx"), providers=["CPUExecutionProvider"])
og = sg.run(None, {"input": x})[0]; ot = st.run(None, {"input": x})[0]
with torch.no_grad():
    tg = gate(torch.from_numpy(x)).numpy(); tt = tnet(torch.from_numpy(x)).numpy()
print("gate max diff", float(np.abs(og-tg).max()), "| type max diff", float(np.abs(ot-tt).max()))
print("types", len(ck["types"]))
for f in ("pipeline_gate.onnx","pipeline_type.onnx"):
    p = os.path.join(BASE,"models",f); print(f, os.path.getsize(p))
