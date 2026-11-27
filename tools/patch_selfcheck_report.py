# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "self_check.py")
t = open(p, encoding="utf-8").read()
if "--report" not in t:
    t = t.replace('''    ap.add_argument("--json", action="store_true")''',
                  '''    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report", action="store_true", help="额外生成战报 HTML")
    ap.add_argument("--open", action="store_true", help="生成后打开战报")''')
    t = t.replace('''    if a.json:
        print(json.dumps({"rules": ev, "arrow": stairs, "strategy": recs}, ensure_ascii=False, indent=1))
        return 0''',
'''    rep = None
    if a.report:
        try:
            from clashlab import battle_report
            rep = battle_report.build(a.layout, th=a.th, open_after=a.open)
        except Exception as e:
            rep = {"ok": False, "error": str(e)[:200]}
    if a.json:
        print(json.dumps({"rules": ev, "arrow": stairs, "strategy": recs, "report": rep}, ensure_ascii=False, indent=1))
        return 0''')
    t = t.replace('''    return 0


if __name__ == "__main__":''',
'''    if rep and rep.get("ok"):
        print("\\n## 战报")
        print("- %s（%d bytes，%s %s）" % (rep["path"], rep["bytes"], rep.get("grade"), rep.get("score")))
    elif rep:
        print("\\n## 战报生成失败：", rep.get("error"))
    return 0


if __name__ == "__main__":''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("self_check --report added")
