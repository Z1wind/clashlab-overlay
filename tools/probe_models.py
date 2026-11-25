# -*- coding: utf-8 -*-
"""解码构建日志 + 拉两个 provider 的 /models 列表（不打印中文，避免控制台编码问题）。"""
import os, json, sys, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm

OUT = os.path.join(BASE, "out", "overlay", "_p2d")
p = os.path.join(OUT, "build_log.txt")
if os.path.exists(p):
    s = open(p, "rb").read().decode("utf-8", "replace")
    open(os.path.join(OUT, "build_log_utf8.txt"), "w", encoding="utf-8").write(s)
    print("log_chars", len(s))

models = {}
for name in ("openai_2", "openai_1"):
    prov = llm.load_provider(name)
    if not prov.get("base") or not prov.get("key"):
        models[name] = {"error": "no provider"}
        continue
    req = urllib.request.Request(prov["base"] + "/models", method="GET")
    req.add_header("Authorization", "Bearer " + prov["key"])
    for k, v in (prov.get("headers") or {}).items():
        req.add_header(str(k), str(v))
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8", "ignore"))
        ids = [m.get("id") for m in body.get("data", [])]
        models[name] = {"base": prov["base"], "count": len(ids), "ids": ids[:80]}
    except Exception as e:
        models[name] = {"base": prov["base"], "error": str(e)[:200]}
json.dump(models, open(os.path.join(OUT, "provider_models.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("models_saved")
for name, v in models.items():
    print(name, v.get("count"), (v.get("error") or "")[:80])
