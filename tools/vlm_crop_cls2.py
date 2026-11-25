# -*- coding: utf-8 -*-
"""VLM 作为「裁剪分类器」测试 v2：quad 来自 out/overlay/_quad_calib/summary.json。"""
import os, sys, json, time, random
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm
from clashlab.geo import Calib

OUT = os.path.join(BASE, "out", "overlay", "_p2d")
MODEL = "glm-5.3-flash"
TYPES = ["town-hall", "eagle-artillery", "monolith", "scattershot", "inferno-tower", "air-defense",
         "x-bow", "multi-archer-tower", "wizard-tower", "bomb-tower", "air-sweeper", "hidden-tesla",
         "spell-tower", "mortar", "archer-tower", "cannon", "firespitter", "ricochet-cannon"]
PROMPT = "这是《部落冲突》单个建筑的裁剪图。只回答一个英文类型名，从下列选一个，不要解释：" + ", ".join(TYPES)
STRIP = ".,:;\"' "


def run(base, n_pick=12):
    s = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))[base]
    q = s["quad"]
    lay = json.load(open(os.path.join(BASE, "bases", "th16", base, "layout.json"), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", base, "base.png"), np.uint8), cv2.IMREAD_COLOR)
    quad = [q["T"], q["R"], q["B"], q["L"]]
    calib = Calib.from_quad([[float(p[0]), float(p[1])] for p in quad], n=int(lay.get("grid", 44)))
    bl = [b for b in lay["buildings"] if b["type"] in TYPES]
    random.seed(11); random.shuffle(bl)
    pick, seen = [], set()
    for b in bl:
        if b["type"] in seen:
            continue
        pick.append(b); seen.add(b["type"])
        if len(pick) >= n_pick:
            break
    res = []
    for b in pick:
        tile = b.get("tile") or b.get("pos") or [b.get("x"), b.get("y")]
        tx, ty = float(tile[0]), float(tile[1])
        px, py = calib.tile_to_px(tx, ty)
        half = 95
        x0, y0 = max(0, int(px - half)), max(0, int(py - half))
        crop = img[y0:y0 + 2 * half, x0:x0 + 2 * half]
        if crop.size == 0:
            continue
        t0 = time.time()
        try:
            b64 = llm.encode_image_jpeg(crop, max_width=380, quality=88)
            msgs = [{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
            text, used = llm.chat(msgs, model=MODEL, max_tokens=20, temperature=0.0, timeout=45, provider="openai_1")
            pred = (text or "").strip().lower().replace(" ", "-").strip(STRIP)
            res.append({"base": base, "truth": b["type"], "pred": pred, "ok": pred == b["type"],
                        "sec": round(time.time() - t0, 1)})
            print(("OK  " if pred == b["type"] else "MISS"), b["type"], "->", pred, "%.0fs" % (time.time() - t0), flush=True)
        except Exception as e:
            res.append({"base": base, "truth": b["type"], "error": str(e)[:150], "sec": round(time.time() - t0, 1)})
            print("ERR ", b["type"], str(e)[:70], flush=True)
    ok = sum(1 for r in res if r.get("ok")); valid = sum(1 for r in res if "error" not in r)
    print("ACC %d/%d valid=%d" % (ok, len(res), valid))
    json.dump({"model": MODEL, "base": base, "n": len(res), "ok": ok, "valid": valid, "rows": res},
              open(os.path.join(OUT, "vlm_crop_cls.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


run("05", 12)
