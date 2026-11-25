# -*- coding: utf-8 -*-
"""openai_2 deepseek-v4.1-flash 视觉复测（A 已证真能看图）：
A2) 四个数字转写（gold/elixir/dark/gems）
B) 三阵整体清单
C) 12 张已知真值裁剪分类
"""
import os, sys, json, time, random
from collections import Counter
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
res = {"provider": PROV, "model": MODEL}


def ask(img, prompt, max_tokens=3000):
    b64 = llm.encode_image_jpeg(img, max_width=1100, quality=85)
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    return llm.chat(msgs, model=MODEL, max_tokens=max_tokens, temperature=0.1, timeout=120,
                    provider=PROV, reasoning_effort="low")


# A2 四个数字
truth4 = {"gold": 12000000, "elixir": 9047975, "dark": 187963, "gems": 2997}
try:
    t0 = time.time()
    text, used = ask(os.path.join(BASE, "out", "overlay", "_auto_label", "game", "pan1.png"),
                     "看截图右上角显示的资源数字（从上到下四条），只输出 JSON："
                     "{\"gold\":整数,\"elixir\":整数,\"dark\":整数,\"gems\":整数}")
    obj = llm.extract_json(text or "") or {}
    hit = {k: str(obj.get(k)) == str(v) for k, v in truth4.items()}
    res["transcribe4"] = {"sec": round(time.time() - t0, 1), "parsed": obj, "truth": truth4, "hit": hit}
    print("A2", "%.1fs" % (time.time() - t0), hit, json.dumps(obj, ensure_ascii=False)[:160], flush=True)
except Exception as e:
    res["transcribe4"] = {"error": str(e)[:200]}
    print("A2 FAIL", str(e)[:120], flush=True)

# B 三阵清单
for base in ("05", "03", "06"):
    try:
        t0 = time.time()
        text, used = ask(os.path.join(BASE, "bases", "th16", base, "base.png"),
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
        lay = json.load(open(os.path.join(BASE, "bases", "th16", base, "layout.json"), encoding="utf-8"))
        tc = Counter(b["type"] for b in lay["buildings"] if b["type"] in TYPES)
        keys = sorted(set(list(tc) + list(pred)))
        rows = [{"type": k, "truth": int(tc.get(k, 0)), "pred": int(pred.get(k, 0))} for k in keys]
        res.setdefault("inventory", []).append({
            "base": base, "ok": isinstance(obj, dict), "sec": round(time.time() - t0, 1),
            "sum_truth": int(sum(tc.values())), "sum_pred": int(sum(pred.values())),
            "pass_le1": sum(1 for r in rows if abs(r["pred"] - r["truth"]) <= 1), "types": len(rows),
            "rows": rows, "raw": (text or "")[:400]})
        print("B", base, "sum", sum(pred.values()), "vs", sum(tc.values()),
              "pass", res["inventory"][-1]["pass_le1"], "/", len(rows), flush=True)
    except Exception as e:
        res.setdefault("inventory", []).append({"base": base, "error": str(e)[:200]})
        print("B", base, "FAIL", str(e)[:100], flush=True)

# C 12 裁剪
try:
    s = json.load(open(os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json"), encoding="utf-8"))["05"]
    q = s["quad"]
    lay = json.load(open(os.path.join(BASE, "bases", "th16", "05", "layout.json"), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", "05", "base.png"), np.uint8), cv2.IMREAD_COLOR)
    calib = Calib.from_quad([[float(p[0]), float(p[1])] for p in [q["T"], q["R"], q["B"], q["L"]]], n=int(lay.get("grid", 44)))
    bl = [b for b in lay["buildings"] if b["type"] in TYPES]
    random.seed(5); random.shuffle(bl)
    pick, seen = [], set()
    for b in bl:
        if b["type"] in seen:
            continue
        pick.append(b); seen.add(b["type"])
        if len(pick) >= 12:
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
            text, used = ask(crop, "单个建筑裁剪图。只输出一个英文类型名，候选：" + ", ".join(TYPES), max_tokens=300)
            pred = (text or "").strip().lower().replace(" ", "-").strip(".,:;\"' ")
            cvalid += 1; good = pred == b["type"]; cok += good
            crows.append({"truth": b["type"], "pred": pred[:60], "ok": good})
            print(("OK  " if good else "MISS"), b["type"], "->", pred[:40], flush=True)
        except Exception as e:
            crows.append({"truth": b["type"], "error": str(e)[:120]})
            print("ERR ", b["type"], str(e)[:70], flush=True)
    res["crop_cls"] = {"ok": cok, "valid": cvalid, "n": len(crows), "rows": crows}
    print("C crop acc", cok, "/", len(crows), "valid", cvalid, flush=True)
except Exception as e:
    res["crop_cls"] = {"error": str(e)[:300]}
    print("C FAIL", str(e)[:150], flush=True)

json.dump(res, open(os.path.join(OUT, "vlm_openai2_vision2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved vlm_openai2_vision2.json")
