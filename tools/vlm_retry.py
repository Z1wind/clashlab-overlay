# -*- coding: utf-8 -*-
"""VLM 路线重试：先探 provider 健康，再用视觉模型读基地截图。每次尝试独立超时。"""
import os, sys, json, time
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm

OUT = os.path.join(BASE, "out", "overlay", "_p2d")
os.makedirs(OUT, exist_ok=True)
res = []

def try_call(tag, fn):
    t0 = time.time()
    try:
        text, used = fn()
        ok = bool(text and text.strip())
        res.append({"tag": tag, "ok": ok, "sec": round(time.time() - t0, 1),
                    "model_used": used, "text": (text or "")[:400]})
        print("[%s] ok=%s used=%s %.1fs :: %s" % (tag, ok, used, time.time() - t0, (text or "")[:80].replace("\n", " ")), flush=True)
    except Exception as e:
        res.append({"tag": tag, "ok": False, "sec": round(time.time() - t0, 1), "error": str(e)[:300]})
        print("[%s] FAIL %.1fs :: %s" % (tag, time.time() - t0, str(e)[:120].replace("\n", " ")), flush=True)

# 1) 文本健康检查
for prov in ("openai_2", "openai_1"):
    try_call("text_" + prov, lambda p=prov: llm.chat(
        [{"role": "user", "content": "只回复两个字：可用"}], provider=p, max_tokens=16, timeout=40))

img = os.path.join(BASE, "bases", "th16", "03", "base.png")
# 2) 视觉：默认链
try_call("vision_default", lambda: llm.chat_vision(
    img, "这张部落冲突截图里，加农炮有几座？只回答数字。", max_tokens=64, timeout=60))
# 3) 视觉：openai_2 + low reasoning + 3000 tokens
def v2():
    b64 = llm.encode_image_jpeg(img)
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": "这张部落冲突截图里，加农炮有几座？只回答数字。"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    return llm.chat(msgs, model=llm.VISION_MODEL, max_tokens=3000, temperature=0.1,
                    timeout=90, provider="openai_2", reasoning_effort="low")
try_call("vision_openai2_low", v2)
# 4) 视觉：openai_1
def v3():
    b64 = llm.encode_image_jpeg(img)
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": "这张部落冲突截图里，加农炮有几座？只回答数字。"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    return llm.chat(msgs, model=llm.VISION_MODEL, max_tokens=800, temperature=0.1,
                    timeout=90, provider="openai_1")
try_call("vision_openai1", v3)

json.dump(res, open(os.path.join(OUT, "vlm_retry.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved vlm_retry.json")
