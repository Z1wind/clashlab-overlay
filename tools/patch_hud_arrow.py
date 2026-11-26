# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# runtime: 在 HUD 阶段图层后画穿云箭
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
if "draw_hud_giant_arrow" not in t:
    anchor = '''                hud_draw.draw_marks(dl, rt.calib, rt.state.marks, 1280.0, 720.0)'''
    add = anchor + '''
                try:
                    from . import giant_arrow_hud
                    _gap = giant_arrow_hud.load_overlay_plan(rt.root)
                    if _gap:
                        giant_arrow_hud.draw_giant_arrow(dl, rt.calib, _gap, 1280.0, 720.0)
                except Exception:
                    pass'''
    if anchor in t:
        t = t.replace(anchor, add, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("runtime hud arrow hooked")
    else:
        print("runtime anchor miss")

# CLI: --emit-overlay 写 config/giant_arrow_overlay.json
p2 = os.path.join(BASE, "tools", "giant_arrow_cli.py")
t2 = open(p2, encoding="utf-8").read()
if "--emit-overlay" not in t2:
    t2 = t2.replace('    ap.add_argument("--json", action="store_true")',
                    '    ap.add_argument("--json", action="store_true")\n'
                    '    ap.add_argument("--emit-overlay", action="store_true",\n'
                    '                    help="写 config/giant_arrow_overlay.json 供 HUD 直接画在游戏上")')
    t2 = t2.replace('''    best = res.get("best")
    if not best:''',
'''    best = res.get("best")
    if a.emit_overlay:
        import time as _t
        if not best:
            print("没有对空目标，无法生成 overlay 计划")
            return
        out = os.path.join(ROOT, "config", "giant_arrow_overlay.json")
        payload = {"from": best["from"], "to": best["to"],
                   "hits": [{"type": h["type"], "tile": h["tile"],
                             "order": h["order"], "perp": h["perp"]} for h in best["hits"]],
                   "summary": best["summary"], "score": best["score"],
                   "ts": _t.strftime("%Y-%m-%dT%H:%M:%S")}
        os.makedirs(os.path.dirname(out), exist_ok=True)
        import json as _json
        _json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("已写 HUD overlay 计划:", out)
        return
    if not best:''')
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("cli emit-overlay added")
