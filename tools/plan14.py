# -*- coding: utf-8 -*-
"""P4：14 号真实数据 -> deepseek-v4.1-flash（chat_robust 3 次重试）-> plan_14_kekejdj.json。
只读 tactics.build_messages / llm；不写 tactics.py/assets.py。"""
import json, os, sys, time
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, ROOT)
from clashlab.overlay import tactics
from clashlab import llm

# 1) staging 全局 info.json = 14 号
src = os.path.join(ROOT, "bases", "th16", "war_20261123", "14_kekejdj", "prebattle", "info.json")
dst = os.path.join(ROOT, "out", "prebattle", "info.json")
info = json.load(open(src, encoding="utf-8"))
json.dump(info, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 2) load_local（th=16 走 assets.stats 覆盖 dps）
doc = tactics.load_local(ROOT)
print("source=", doc.get("source"), "rows=", len(doc.get("rows") or []))
for r in doc.get("rows", []):
    print("  ", r["name"], r["tile"], "dps", r["dps"])

msgs = tactics.build_messages(doc, goal="三星")
t0 = time.perf_counter()
res = llm.chat_robust(msgs, model="deepseek-v4.1-flash", temperature=0.25,
                      max_tokens=560, timeout=40, max_attempts=3)
elapsed = round(time.perf_counter() - t0, 2)

out = {
    "ok": bool(res.get("ok")),
    "goal": "三星",
    "sel": (tactics.selected(doc) or {}).get("name", ""),
    "model": res.get("model_used", ""),
    "elapsed": elapsed,
    "attempts": res.get("attempts", 0),
    "retry_stage": res.get("stage", ""),
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "source_layout": "war_20261123/14_kekejdj",
    "context_rows": doc.get("rows"),
    "text": res.get("text", ""),
    "error": res.get("last_reason", "") or res.get("code", ""),
}
odir = os.path.join(ROOT, "out", "overlay", "tactics")
os.makedirs(odir, exist_ok=True)
with open(os.path.join(odir, "plan_14_kekejdj.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
print("ok=", out["ok"], "model=", out["model"], "attempts=", out["attempts"], "elapsed=", elapsed)
print(out["text"][:400])
