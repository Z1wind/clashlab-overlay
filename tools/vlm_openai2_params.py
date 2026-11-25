# -*- coding: utf-8 -*-
"""参数探测：openai_2 + 图像为何「空 content」。用同一张裁剪试多种参数组合。"""
import os, sys, json, time
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm
from clashlab.geo import Calib
OUT = os.path.join(BASE, "out", "overlay", "_p2d")
PROV, MODEL = "openai_2", "deepseek-v4.1-flash"
TYPES = ["town-hall", "eagle-artillery", "monolith", "scattershot", "inferno-tower", "air-defense",
         "x-bow", "multi-archer-tower", "wizard-tower", "bomb-tower", "air-sweeper", "hidden-tesla",
         "spell-tower", "mortar", "archer-tower", "cannon", "firespitter", "ricochet-cannon"]

s = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))["05"]
q = s["quad"]
lay = json.load(open(os.path.join(BASE, "bases", "th16", "05", "layout.json"), encoding="utf-8"))
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", "05", "base.png"), np.uint8), cv2.IMREAD_COLOR)
calib = Calib.from_quad([[float(p[0]), float(p[1])] for p in [q["T"], q["R"], q["B"], q["L"]]], n=int(lay.get("grid", 44)))
target = next(b for b in lay["buildings"] if b["type"] == "inferno-tower")
tile = target.get("tile") or [target.get("x"), target.get("y")]
px, py = calib.tile_to_px(float(tile[0]), float(tile[1]))
half = 95
crop = img[int(py - half):int(py + half), int(px - half):int(px + half)]
b64 = llm.encode_image_jpeg(crop, max_width=420, quality=90)
prompt = "这是《部落冲突》单个建筑的裁剪图。只回答一个英文类型名，候选：" + ", ".join(TYPES)

variants = [
    ("low_2000", dict(reasoning_effort="low", max_tokens=2000)),
    ("none_2000", dict(reasoning_effort=None, max_tokens=2000)),
    ("none_4000", dict(reasoning_effort=None, max_tokens=4000)),
    ("low_4000", dict(reasoning_effort="low", max_tokens=4000)),
]
res = []
for tag, kw in variants:
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    t0 = time.time()
    try:
        text, used = llm.chat(msgs, model=MODEL, temperature=0.1, timeout=100, provider=PROV, **kw)
        res.append({"tag": tag, "sec": round(time.time() - t0, 1), "text": (text or "")[:200]})
        print(tag, "%.1fs" % (time.time() - t0), "len=", len(text or ""), (text or "")[:60].replace("\n", " "), flush=True)
    except Exception as e:
        res.append({"tag": tag, "sec": round(time.time() - t0, 1), "error": str(e)[:160]})
        print(tag, "FAIL", str(e)[:90], flush=True)
json.dump({"truth": "inferno-tower", "variants": res}, open(os.path.join(OUT, "vlm_openai2_params.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved")
