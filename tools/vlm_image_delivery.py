# -*- coding: utf-8 -*-
"""判定 VLM 是否真的收到图片：让它转写已知截图上的资源数字（真值已知）。"""
import os, sys, json, time
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm
OUT = os.path.join(BASE, "out", "overlay", "_p2d")
img = os.path.join(BASE, "out", "overlay", "_auto_label", "game", "pan1.png")
truth = {"gold": 12000000, "elixir": 9047975, "gems": 2997}
res = []
prompt = ("看这张《部落冲突》截图，右上角有三个资源数字。请只输出 JSON："
          "{\"gold\":整数,\"elixir\":整数,\"gems\":整数}，不要解释。")
for model in ("glm-5.3-flash", "mimo-v2.6-pro", "glm-5.3"):
    b64 = llm.encode_image_jpeg(img, max_width=1100, quality=85)
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    t0 = time.time()
    try:
        text, used = llm.chat(msgs, model=model, max_tokens=300, temperature=0.1, timeout=60, provider="openai_1")
        obj = llm.extract_json(text or "")
        got = obj if isinstance(obj, dict) else {}
        hit = {k: (str(got.get(k)) == str(v)) for k, v in truth.items()}
        res.append({"model": model, "sec": round(time.time() - t0, 1), "raw": (text or "")[:300],
                    "parsed": got, "truth": truth, "hit": hit})
        print(model, "%.1fs" % (time.time() - t0), "hit=", hit, json.dumps(got, ensure_ascii=False)[:120], flush=True)
    except Exception as e:
        res.append({"model": model, "sec": round(time.time() - t0, 1), "error": str(e)[:200]})
        print(model, "FAIL", str(e)[:80], flush=True)
json.dump(res, open(os.path.join(OUT, "vlm_image_delivery.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved")
