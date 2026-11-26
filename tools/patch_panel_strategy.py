# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
# 1) prebattle: add strategies
p = os.path.join(BASE, 'clashlab', 'prebattle.py')
t = open(p, encoding='utf-8').read()
anchor = '''    # 把 report / rules 挂在私有键上供 brief 复用，不进对外契约字段'''
add = '''    # --- 6.6 布阵 -> 兵种搭配推荐（弱点驱动；失败不阻断简报）---
    try:
        if lay_doc:
            import re as _re
            from . import strategy as _strategy
            _name = str(lay_doc.get("name") or "") + " " + str(lay_doc.get("note") or "")
            _m = _re.search(r"th(\\d{1,2})", _name, _re.I)
            _th = int(_m.group(1)) if _m else 16
            _recs = _strategy.recommend(lay_doc, th=_th)
            if _recs:
                info["strategies"] = _recs[:2]
                _first = _recs[0]
                info["strategy_summary"] = "%s（%s）" % (_first.get("name"), _first.get("reason"))
    except Exception:  # noqa: BLE001 - 推荐失败不影响简报
        pass

''' + anchor
if 'strategy_summary' in t:
    print('prebattle already patched')
elif anchor in t:
    t = t.replace(anchor, add, 1)
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('prebattle patched')
else:
    print('prebattle anchor miss')

# 2) pages: strategy line after sim line
p2 = os.path.join(BASE, 'clashlab', 'overlay', 'pages.py')
t2 = open(p2, encoding='utf-8').read()
old = '''    imgui.text_colored(imgui.ImVec4(*SUBTLE), _sim_line(state))
    y += 20.0'''
new = '''    imgui.text_colored(imgui.ImVec4(*SUBTLE), _sim_line(state))
    y += 20.0
    imgui.text_colored(imgui.ImVec4(*SUBTLE), _strategy_line(state))
    y += 20.0'''
if '_strategy_line' in t2:
    print('pages already patched')
elif old in t2:
    t2 = t2.replace(old, new, 1)
    helper = '''
_STRATEGY_CACHE = {"key": None, "line": ""}


def _fmt_strategy_info(info):
    """把 prebattle info 里的 strategies 压成一行文案（纯函数，便于测试）。"""
    if not isinstance(info, dict):
        return "推荐：无数据"
    summary = info.get("strategy_summary")
    if summary:
        return "推荐：" + str(summary)[:42]
    recs = info.get("strategies")
    if isinstance(recs, list) and recs and isinstance(recs[0], dict):
        r0 = recs[0]
        return "推荐：" + ("%s（%s）" % (r0.get("name"), r0.get("reason")))[:42]
    return "推荐：无数据"


def _strategy_line(state):
    """v11-战绩推荐行：读 out/prebattle/info.json（按 mtime 缓存），失败给「无数据」。"""
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root, "out", "prebattle", "info.json")
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            return "推荐：无数据"
        key = (path, mtime)
        if _STRATEGY_CACHE.get("key") == key:
            return _STRATEGY_CACHE.get("line") or "推荐：无数据"
        with open(path, "r", encoding="utf-8") as f:
            info = json.load(f)
        line = _fmt_strategy_info(info)
        _STRATEGY_CACHE["key"] = key
        _STRATEGY_CACHE["line"] = line
        return line
    except Exception:
        return "推荐：无数据"


'''
    t2 = t2.replace('def _sim_line(state):', helper + 'def _sim_line(state):', 1)
    open(p2, 'w', encoding='utf-8', newline=chr(10)).write(t2)
    print('pages patched')
else:
    print('pages anchor miss')

# 3) pages needs json import
if 'import json' not in t2.split(chr(10))[0:40][0:40] and 'import json' not in t2[:2000]:
    t2 = open(p2, encoding='utf-8').read()
    if 'import json' not in t2:
        t2 = t2.replace('import os', 'import json' + chr(10) + 'import os', 1)
        open(p2, 'w', encoding='utf-8', newline=chr(10)).write(t2)
        print('pages import json added')
