# -*- coding: utf-8 -*-
"""VLM 多模型候选探测：qianye 的 14 个模型里挑可能支持图像输入的，各试一次短请求。"""
import os, sys, json, time
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm
OUT = os.path.join(BASE, "out", "overlay", "_p2d")
img = os.path.join(BASE, "bases", "th16", "03", "base.png")
b64 = llm.encode_image_jpeg(img, max_width=800, quality=70)
msgs = [{"role": "user", "content": [
    {"type": "text", "text": "这张游戏截图里有几座加农炮？只回数字。"},
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
cands = ["deepseek-v4-flash-vision-exp", "glm-5.3", "glm-5.3-flash", "kimi-k3-1",
         "kimi-k3.1-pro", "minimax-m3", "minimax-m3.1-flash", "hy4-preview", "mimo-v2.6-pro"]
res = []
for m in cands:
    t0 = time.time()
    try:
        text, used = llm.chat(msgs, model=m, max_tokens=200, temperature=0.1, timeout=45, provider="openai_1")
        ok = bool(text and text.strip())
        res.append({"model": m, "ok": ok, "sec": round(time.time() - t0, 1), "used": used, "text": (text or "")[:120]})
        print("OK ", m, "%.1fs" % (time.time() - t0), (text or "")[:40].replace("\n", " "), flush=True)
    except Exception as e:
        res.append({"model": m, "ok": False, "sec": round(time.time() - t0, 1), "error": str(e)[:160]})
        print("ERR", m, "%.1fs" % (time.time() - t0), str(e)[:80].replace("\n", " "), flush=True)
json.dump(res, open(os.path.join(OUT, "vlm_models_probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved")
