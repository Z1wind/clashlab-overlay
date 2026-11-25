# -*- coding: utf-8 -*-
"""VLM 读基地测试（重试 VLM 路线）：
A) 鉴别题（证明模型真的看图，不是瞎猜）
B) 清单题（3 阵 × 防御建筑计数，对比 layout.json 真值）
"""
import os, sys, json, time
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm
OUT = os.path.join(BASE, "out", "overlay", "_p2d")
MODEL = "glm-5.3"
TYPES = ["town-hall", "eagle-artillery", "monolith", "scattershot", "inferno-tower", "air-defense",
         "x-bow", "multi-archer-tower", "wizard-tower", "bomb-tower", "air-sweeper", "hidden-tesla",
         "spell-tower", "mortar", "archer-tower", "cannon", "firespitter", "ricochet-cannon"]
res = {"model": MODEL, "discriminator": [], "inventory": []}


def ask(img, prompt, max_tokens=800):
    b64 = llm.encode_image_jpeg(img, max_width=1100, quality=82)
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
    return llm.chat(msgs, model=MODEL, max_tokens=max_tokens, temperature=0.1, timeout=90, provider="openai_1")


def truth_counts(base):
    lay = json.load(open(os.path.join(BASE, "bases", "th16", base, "layout.json"), encoding="utf-8"))
    from collections import Counter
    return Counter(b["type"] for b in lay["buildings"] if b["type"] != "wall")


# A) 鉴别题：大本营在哪个象限（03 真值：x=1029/2622 右半、y=578/1206 下半 → 右下）
img03 = os.path.join(BASE, "bases", "th16", "03", "base.png")
try:
    t, u = ask(img03, "只回答一个词：这张部落冲突截图里，大本营（Town Hall）位于画面的哪个象限？可选：左上/右上/左下/右下。")
    res["discriminator"].append({"q": "TH象限(真值=右下)", "a": t, "model": u})
    print("D1:", (t or "")[:40], flush=True)
except Exception as e:
    res["discriminator"].append({"q": "TH象限", "error": str(e)[:160]})
    print("D1 FAIL", str(e)[:100], flush=True)
try:
    t, u = ask(img03, "只回答一个词：画面里数量最多的防御建筑是哪一类？（加农炮/箭塔/法师塔/X连弩/地狱塔/防空火箭 之一）")
    res["discriminator"].append({"q": "数量最多的防御(真值=x-bow 9 座)", "a": t, "model": u})
    print("D2:", (t or "")[:40], flush=True)
except Exception as e:
    res["discriminator"].append({"q": "最多防御", "error": str(e)[:160]})
    print("D2 FAIL", str(e)[:100], flush=True)

# B) 清单题
prompt = ("这是《部落冲突》TH16 基地的侦察截图。只统计防御建筑，不要墙/装饰/资源建筑。"
          "请只输出 JSON，格式：{\"buildings\":[{\"type\":\"英文类型\",\"count\":整数}]}。"
          "允许的英文类型：" + ", ".join(TYPES) + "。")
for base in ("03", "05", "06"):
    img = os.path.join(BASE, "bases", "th16", base, "base.png")
    tc = truth_counts(base)
    try:
        t, u = ask(img, prompt, max_tokens=900)
        obj = llm.extract_json(t or "")
        pred = {}
        if isinstance(obj, dict):
            for it in obj.get("buildings", []) or []:
                k = str(it.get("type", "")).strip().lower().replace(" ", "-")
                try:
                    pred[k] = int(it.get("count", 0))
                except Exception:
                    pass
        keys = sorted(set(list(tc.keys()) + list(pred.keys())))
        rows = [{"type": k, "truth": int(tc.get(k, 0)), "pred": int(pred.get(k, 0)),
                 "diff": int(pred.get(k, 0)) - int(tc.get(k, 0))} for k in keys]
        pass_n = sum(1 for r in rows if abs(r["diff"]) <= 1)
        res["inventory"].append({"base": base, "ok": isinstance(obj, dict), "model": u,
                                 "raw": (t or "")[:600], "rows": rows,
                                 "pass_le1": pass_n, "total_types": len(rows),
                                 "sum_truth": int(sum(tc.values())), "sum_pred": int(sum(pred.values()))})
        print("INV", base, "ok", isinstance(obj, dict), "pass", pass_n, "/", len(rows), flush=True)
    except Exception as e:
        res["inventory"].append({"base": base, "error": str(e)[:200]})
        print("INV", base, "FAIL", str(e)[:100], flush=True)

json.dump(res, open(os.path.join(OUT, "vlm_base_read.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved vlm_base_read.json")
