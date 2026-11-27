# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "enemy_pipeline.py")
t = open(p, encoding="utf-8").read()
if "layout_rules" not in t:
    anchor = '    # 2) 穿云箭自动选线'
    add = ('    # 1b) 规则化评分（可解释规则集，含墙体逐格校验）\n'
           '    try:\n'
           '        from clashlab import layout_rules\n'
           '        report["rules_eval"] = layout_rules.evaluate(lay)\n'
           '    except Exception as e:\n'
           '        report["rules_error"] = str(e)[:160]\n\n')
    if anchor in t:
        t = t.replace(anchor, add + anchor, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("pipeline: rules_eval added")
    else:
        print("anchor miss")
else:
    print("already")
