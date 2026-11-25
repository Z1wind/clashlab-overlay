# -*- coding: utf-8 -*-
"""探针：视觉大模型能否直接读出基地防御建筑清单（对比 layout.json 真值）。
仓库里已有 clashlab.llm.chat_vision + VISION_MODEL，此前从未用于识别。
"""
import os, sys, json, time
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import llm

lay = json.load(open(os.path.join(BASE, "bases", "th16", "03", "layout.json"), encoding="utf-8"))
from collections import Counter
truth = Counter(b["type"] for b in lay["buildings"])
prompt = (
    "这是《部落冲突》TH16 战斗地图的侦察截图。请只输出 JSON，不要解释，格式：\n"
    '{"buildings":[{"type":"英文建筑类别","count":整数}]}\n'
    "只统计防御建筑（加农炮/箭塔/法师塔/迫击炮/防空/空气炮/特斯拉/X连弩/地狱塔/炸弹塔/鹰火炮/投石炮/多重箭塔/法术塔/巨石碑/喷火器/弹射加农炮/大本营/部落城堡），不要墙和装饰。"
)
img = os.path.join(BASE, "bases", "th16", "03", "base.png")
t0 = time.time()
try:
    text, used = llm.chat_vision(img, prompt, max_tokens=1200)
    dt = time.time() - t0
    print("provider:", used, "sec:", round(dt, 1))
    print("RAW:", (text or "")[:1500])
    out = {"provider": used, "sec": round(dt, 1), "raw": text, "truth": dict(truth)}
    json.dump(out, open(os.path.join(BASE, "out", "overlay", "_p2c", "vlm_base_read_probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
except Exception as e:
    print("VLM CALL FAILED:", repr(e)[:400])
