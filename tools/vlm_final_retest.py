# -*- coding: utf-8 -*-
"""VLM 最终复测：修掉上一轮的 max_tokens 过小（20）导致的「空 content」。
A) 8 个已知真值裁剪 → 只回答类型（max_tokens=400）
B) 05 阵整体清单（max_tokens=1500，要求先描述再给 JSON）
"""
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
STRIP = ".,:;\"' "


def ask_crop(crop, prompt, max_tokens=400):
    b64 = llm.encode_image_jpeg(crop, max_width=420, quality=90)
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    return llm.chat(msgs, model=MODEL, max_tokens=max_tokens, temperature=0.0, timeout=60, provider="openai_1")


def main():
    s = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))["05"]
    q = s["quad"]
    lay = json.load(open(os.path.join(BASE, "bases", "th16", "05", "layout.json"), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", "05", "base.png"), np.uint8), cv2.IMREAD_COLOR)
    calib = Calib.from_quad([[float(p[0]), float(p[1])] for p in [q["T"], q["R"], q["B"], q["L"]]],
                            n=int(lay.get("grid", 44)))
    bl = [b for b in lay["buildings"] if b["type"] in TYPES]
    random.seed(5); random.shuffle(bl)
    pick, seen = [], set()
    for b in bl:
        if b["type"] in seen:
            continue
        pick.append(b); seen.add(b["type"])
        if len(pick) >= 8:
            break
    prompt = ("这是《部落冲突》单个建筑的裁剪图。先在心里判断，然后只输出一个英文类型名（不要解释），"
              "候选：" + ", ".join(TYPES))
    rows = []
    ok = valid = 0
    for b in pick:
        tile = b.get("tile") or b.get("pos") or [b.get("x"), b.get("y")]
        px, py = calib.tile_to_px(float(tile[0]), float(tile[1]))
        half = 95
        crop = img[max(0, int(py - half)):int(py + half), max(0, int(px - half)):int(px + half)]
        if crop.size == 0:
            continue
        t0 = time.time()
        try:
            text, used = ask_crop(crop, prompt, 400)
            pred = (text or "").strip().lower().replace(" ", "-").strip(STRIP)
            valid += 1
            good = pred == b["type"]
            ok += good
            rows.append({"truth": b["type"], "pred": pred[:60], "ok": good, "sec": round(time.time() - t0, 1)})
            print(("OK  " if good else "MISS"), b["type"], "->", pred[:40], "%.0fs" % (time.time() - t0), flush=True)
        except Exception as e:
            rows.append({"truth": b["type"], "error": str(e)[:120], "sec": round(time.time() - t0, 1)})
            print("ERR ", b["type"], str(e)[:80], flush=True)
    print("CROP ACC %d/%d valid=%d" % (ok, len(rows), valid))
    # B) 整体清单
    inv_prompt = ("这是《部落冲突》TH16 基地侦察图。先逐区域检查，再只输出 JSON："
                  "{\"buildings\":[{\"type\":\"英文类型\",\"count\":整数}]}，只统计防御建筑（不含墙/资源/装饰）。"
                  "候选：" + ", ".join(TYPES))
    b64 = llm.encode_image_jpeg(os.path.join(BASE, "bases", "th16", "05", "base.png"), max_width=1100, quality=85)
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": inv_prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    inv = {}
    try:
        text, used = llm.chat(msgs, model=MODEL, max_tokens=1500, temperature=0.1, timeout=90, provider="openai_1")
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
        tc = Counter(b["type"] for b in lay["buildings"] if b["type"] in TYPES)
        keys = sorted(set(list(tc) + list(pred)))
        rows2 = [{"type": k, "truth": int(tc.get(k, 0)), "pred": int(pred.get(k, 0))} for k in keys]
        inv = {"ok": isinstance(obj, dict), "sum_truth": int(sum(tc.values())), "sum_pred": int(sum(pred.values())),
               "pass_le1": sum(1 for r in rows2 if abs(r["pred"] - r["truth"]) <= 1), "types": len(rows2), "rows": rows2}
        print("INV ok", inv["ok"], "sum", inv["sum_pred"], "vs", inv["sum_truth"], "pass_le1", inv["pass_le1"], "/", inv["types"], flush=True)
    except Exception as e:
        inv = {"error": str(e)[:150]}
        print("INV FAIL", str(e)[:100], flush=True)
    json.dump({"model": MODEL, "crop_rows": rows, "crop_ok": ok, "crop_valid": valid, "inventory": inv},
              open(os.path.join(OUT, "vlm_final_retest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


main()
