# -*- coding: utf-8 -*-
"""openai_2 视觉裁剪分类：收紧裁剪 + 明确「只看正中心」的 prompt，max_tokens=2000。"""
import os, sys, json, time, random
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
res = []
for base in ("05", "03"):
    s = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))[base]
    q = s["quad"]
    lay = json.load(open(os.path.join(BASE, "bases", "th16", base, "layout.json"), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", base, "base.png"), np.uint8), cv2.IMREAD_COLOR)
    calib = Calib.from_quad([[float(p[0]), float(p[1])] for p in [q["T"], q["R"], q["B"], q["L"]]], n=int(lay.get("grid", 44)))
    bl = [b for b in lay["buildings"] if b["type"] in TYPES]
    random.seed(5); random.shuffle(bl)
    pick, seen = [], set()
    for b in bl:
        if b["type"] in seen:
            continue
        pick.append(b); seen.add(b["type"])
        if len(pick) >= 8:
            break
    for b in pick:
        tile = b.get("tile") or b.get("pos") or [b.get("x"), b.get("y")]
        px, py = calib.tile_to_px(float(tile[0]), float(tile[1]))
        half = 70
        crop = img[int(py - half):int(py + half), int(px - half):int(px + half)]
        if crop.size == 0:
            continue
        b64 = llm.encode_image_jpeg(crop, max_width=520, quality=92)
        msgs = [{"role": "user", "content": [
            {"type": "text", "text": "这是《部落冲突》单栋建筑的裁剪图。只回答图片正中心那栋建筑的英文类型名（候选：" + ", ".join(TYPES) + "），不要解释。"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
        t0 = time.time()
        try:
            text, used = llm.chat(msgs, model=MODEL, max_tokens=2000, temperature=0.1, timeout=100,
                                  provider=PROV, reasoning_effort="low")
            pred = (text or "").strip().lower().replace(" ", "-").strip(".,:;\"' ")
            good = pred == b["type"]
            res.append({"base": base, "truth": b["type"], "pred": pred[:60], "ok": good, "sec": round(time.time() - t0, 1)})
            print(("OK  " if good else "MISS"), base, b["type"], "->", pred[:40], "%.0fs" % (time.time() - t0), flush=True)
        except Exception as e:
            res.append({"base": base, "truth": b["type"], "error": str(e)[:150]})
            print("ERR ", base, b["type"], str(e)[:70], flush=True)
ok = sum(1 for r in res if r.get("ok")); valid = sum(1 for r in res if "error" not in r)
print("ACC %d/%d valid=%d" % (ok, len(res), valid))
json.dump({"provider": PROV, "model": MODEL, "ok": ok, "valid": valid, "n": len(res), "rows": res},
          open(os.path.join(OUT, "vlm_openai2_crop2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
