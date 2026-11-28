# -*- coding: utf-8 -*-
import json, os, sys, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 96
class Net(nn.Module):
    def __init__(self, n):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2); self.head = nn.Linear(192, n)
    def forward(self, x): return self.head(self.drop(self.f(x).flatten(1)))
class Emb(nn.Module):
    def __init__(self, n, dim=128):
        super().__init__()
        def blk(i,o): return nn.Sequential(nn.Conv2d(i,o,3,padding=1), nn.BatchNorm2d(o), nn.ReLU(True), nn.MaxPool2d(2))
        self.f = nn.Sequential(blk(3,32), blk(32,64), blk(64,128), blk(128,192), nn.AdaptiveAvgPool2d(1))
        self.drop = nn.Dropout(0.2); self.proj = nn.Linear(192, dim); self.weight = nn.Parameter(torch.randn(n, dim))
    def forward(self, x): return F.normalize(self.proj(self.drop(self.f(x).flatten(1))), dim=1)
def main():
    gk = torch.load(os.path.join(BASE,"models","hybrid_gate.pt"), map_location="cpu")
    ek = torch.load(os.path.join(BASE,"models","hybrid_emb.pt"), map_location="cpu")
    gate = Net(2); gate.load_state_dict(gk["model"]); gate.eval()
    emb = Emb(ek["nc"]); emb.load_state_dict(ek["model"]); emb.eval()
    dummy = torch.randn(4,3,S,S)
    torch.onnx.export(gate, dummy, os.path.join(BASE,"models","hybrid_gate.onnx"), input_names=["input"], output_names=["logits"],
                      opset_version=18, dynamo=False, dynamic_axes={"input":{0:"batch"},"logits":{0:"batch"}})
    torch.onnx.export(emb, dummy, os.path.join(BASE,"models","hybrid_emb.onnx"), input_names=["input"], output_names=["emb"],
                      opset_version=18, dynamo=False, dynamic_axes={"input":{0:"batch"},"emb":{0:"batch"}})
    print("exported")
    import onnxruntime as ort
    x = np.random.rand(3,3,S,S).astype(np.float32)
    og = ort.InferenceSession(os.path.join(BASE,"models","hybrid_gate.onnx"), providers=["CPUExecutionProvider"]).run(None, {"input": x})[0]
    oe = ort.InferenceSession(os.path.join(BASE,"models","hybrid_emb.onnx"), providers=["CPUExecutionProvider"]).run(None, {"input": x})[0]
    with torch.no_grad():
        tg = gate(torch.from_numpy(x)).numpy(); te = emb(torch.from_numpy(x)).numpy()
    print("diff gate", float(np.abs(og-tg).max()), "emb", float(np.abs(oe-te).max()))
    for f in ("hybrid_gate.onnx","hybrid_emb.onnx","hybrid_protos.npz","hybrid_meta.json"):
        print(f, os.path.getsize(os.path.join(BASE,"models",f)))
if __name__ == "__main__":
    main()
