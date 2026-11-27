# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
if "_opponent_th_suffix" not in t:
    anchor = "def _opponent_line(state):"
    add = '''def _opponent_th_suffix(payload):
    """把 clan_th_dist 压成一行后缀：部落 TH16×3 · TH15×5。"""
    try:
        dist = (payload or {}).get("clan_th_dist") or {}
        if not isinstance(dist, dict) or not dist:
            return ""
        items = sorted(dist.items(), key=lambda kv: -int(kv[0]))[:3]
        parts = ["TH%s×%s" % (k, v) for k, v in items]
        return " · 部落 " + " ".join(parts)
    except Exception:
        return ""


'''
    if anchor in t:
        t = t.replace(anchor, add + anchor, 1)
        t = t.replace("        line = _fmt_ocr_payload(payload)\n",
                      "        line = _fmt_ocr_payload(payload) + _opponent_th_suffix(payload)\n", 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("panel TH suffix added")
    else:
        print("anchor miss")
else:
    print("already")
