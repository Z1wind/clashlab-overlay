# -*- coding: utf-8 -*-
"""按用户提示重测：openai_2 的 deepseek-v4.1-flash 是否具备视觉能力。
A) 转写已知资源数字（真值 12,000,000 / 9,047,975 / 2,997）
B) 若 A 通过：base 05 整体建筑清单
C) 若 A 通过：8 张已知真值裁剪的分类
"""
import os, sys, json, time
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm
from clashlab.geo import Calib

OUT = os.path.join(BASE, "out", "overlay", "_p2d")
PROV = "openai_2"
MODEL = "deepseek-v4.1-flash"
TYPES = ["town-hall", "eagle-artillery", "monolith", "scattershot", "inferno-tower", "air-defense",
         "x-bow", "multi-archer-tower", "wizard-tower", "bomb-tower", "air-sweeper", "hidden-tesla",
         "spell-tower", "mortar", "archer-tower", "cannon", "firespitter", "ricochet-cannon"]
res = {"provider": PROV, "model": MODEL}


def ask(img, prompt, max_tokens=3000):
    b64 = llm.encode_image_jpeg(img, max_width=1100, quality=85)
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    return llm.chat(msgs, model=MODEL, max_tokens=max_tokens, temperature=0.1, timeout=120,
                    provider=PROV, reasoning_effort="low")


# A) 转写
img1 = os.path.join(BASE, "out", "overlay", "_auto_label", "game", "pan1.png")
truth = {"gold": 12000000, "elixir": 9047975, "gems": 2997}
vision_ok = False
try:
    t0 = time.time()
    text, used = ask(img1, "看这张部落冲突截图右上角的三个资源数字，只输出 JSON：{\"gold\":整数,\"elixir\":整数,\"gems\":整数}")
    obj = llm.extract_json(text or "")
    got = obj if isinstance(obj, dict) else {}
    hit = {k: (str(got.get(k)) == str(v)) for k, v in truth.items()}
    vision_ok = all(hit.values())
    res["transcribe"] = {"sec": round(time.time() - t0, 1), "raw": (text or "")[:400], "parsed": got,
                         "truth": truth, "hit": hit, "vision_ok": vision_ok}
    print("A transcribe", "%.1fs" % (time.time() - t0), "vision_ok=", vision_ok, json.dumps(got, ensure_ascii=False)[:150], flush=True)
except Exception as e:
    res["transcribe"] = {"error": str(e)[:300]}
    print("A FAIL", str(e)[:150], flush=True)

if vision_ok:
    # B) 整体清单 base 05
    try:
        t0 = time.time()
        text, used = ask(os.path.join(BASE, "bases", "th16", "05", "base.png"),
                         "这是TH16基地侦察图。先逐区域看，最后只输出JSON：{\"buildings\":[{\"type\":\"英文类型\",\"count\":整数}]}，"
                         "只统计防御建筑（不含墙/资源/装饰）。候选：" + ", ".join(TYPES), max_tokens=3000)
        obj = llm.extract_json(text or "")
        pred = {}
        if isinstance(obj, dict):
            for it in obj.get("buildings", []) or []:
                k = str(it.get("type", "")).strip().lower().replace(" ", "-")
                try:
                    pred[k] = int(it.get("count", 0))
                except Exception:
                    pass
        from collections import Counter
        lay = json.load(open(os.path.join(BASE, "bases", "th16", "05", "layout.json"), encoding="utf-8"))
        tc = Counter(b["type"] for b in lay["buildings"] if b["type"] in TYPES)
        keys = sorted(set(list(tc) + list(pred)))
        rows = [{"type": k, "truth": int(tc.get(k, 0)), "pred": int(pred.get(k, 0))} for k in keys]
        res["inventory_05"] = {"sec": round(time.time() - t0, 1), "ok": isinstance(obj, dict),
                               "sum_truth": int(sum(tc.values())), "sum_pred": int(sum(pred.values())),
                               "pass_le1": sum(1 for r in rows if abs(r["pred"] - r["truth"]) <= 1),
                               "types": len(rows), "rows": rows, "raw": (text or "")[:500]}
        print("B inventory sum", sum(pred.values()), "vs", sum(tc.values()), "pass", res["inventory_05"]["pass_le1"], "/", len(rows), flush=True)
    except Exception as e:
        res["inventory_05"] = {"error": str(e)[:300]}
        print("B FAIL", str(e)[:150], flush=True)
    # C) 8 张裁剪分类
    try:
        s = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))["05"]
        q = s["quad"]
        lay = json.load(open(os.path.join(BASE, "bases", "th16", "05", "layout.json"), encoding="utf-8"))
        img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", "05", "base.png"), np.uint8), cv2.IMREAD_COLOR)
        calib = Calib.from_quad([[float(p[0]), float(p[1])] for p in [q["T"], q["R"], q["B"], q["L"]]], n=int(lay.get("grid", 44)))
        bl = [b for b in lay["buildings"] if b["type"] in TYPES]
        import random
        random.seed(5); random.shuffle(bl)
        pick, seen = [], set()
        for b in bl:
            if b["type"] in seen:
                continue
            pick.append(b); seen.add(b["type"])
            if len(pick) >= 8:
                break
        crows, cok, cvalid = [], 0, 0
        for b in pick:
            tile = b.get("tile") or b.get("pos") or [b.get("x"), b.get("y")]
            px, py = calib.tile_to_px(float(tile[0]), float(tile[1]))
            half = 95
            crop = img[max(0, int(py - half)):int(py + half), max(0, int(px - half)):int(px + half)]
            if crop.size == 0:
                continue
            try:
                text, used = ask(crop, "单个建筑裁剪图，只输出一个英文类型名，候选：" + ", ".join(TYPES), max_tokens=300)
                pred = (text or "").strip().lower().replace(" ", "-").strip(".,:;\"' ")
                cvalid += 1; good = pred == b["type"]; cok += good
                crows.append({"truth": b["type"], "pred": pred[:60], "ok": good})
                print(("OK  " if good else "MISS"), b["type"], "->", pred[:40], flush=True)
            except Exception as e:
                crows.append({"truth": b["type"], "error": str(e)[:120]})
                print("ERR ", b["type"], str(e)[:70], flush=True)
        res["crop_cls"] = {"ok": cok, "valid": cvalid, "rows": crows}
        print("C crop acc", cok, "/", len(crows), "valid", cvalid, flush=True)
    except Exception as e:
        res["crop_cls"] = {"error": str(e)[:300]}
        print("C FAIL", str(e)[:150], flush=True)

json.dump(res, open(os.path.join(OUT, "vlm_openai2_vision.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved vlm_openai2_vision.json")
