# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) server: /units 路由
p = os.path.join(BASE, "tools", "annotate_web.py")
t = open(p, encoding="utf-8").read()
if 'u.path == "/units"' not in t:
    anchor = '''        if u.path == "/image":'''
    add = '''        if u.path == "/units":
            up = os.path.join(ROOT, "out", "units.html")
            if not os.path.exists(up):
                subprocess.run([sys.executable, "-u", os.path.join(ROOT, "tools", "build_units_page.py")],
                               capture_output=True, timeout=120)
            if os.path.exists(up):
                with open(up, "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            return self._send(404, "units page not built")
        if u.path == "/image":'''
    if anchor in t:
        t = t.replace(anchor, add, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("server /units added")
    else:
        print("server anchor miss")

# 2) panel: battle sim line
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
if "def _battle_sim_line(" not in t2:
    anchor2 = "def _opponent_th_suffix(payload):"
    add2 = '''_SIM_CACHE = {}


def _battle_sim_line(state):
    """研究页进攻模拟行（按布局指纹缓存；默认 hybrid-miner 配比）。"""
    try:
        lay = getattr(state, "layout", None)
        if not isinstance(lay, dict):
            lay = getattr(state, "Layout", None)
        if not isinstance(lay, dict) or not (lay.get("buildings") or []):
            return _T("模拟：无阵型数据", "Sim: no layout")
        key = (lay.get("name"), len(lay.get("buildings") or []), len(lay.get("walls") or []))
        if _SIM_CACHE.get("key") == key:
            return _SIM_CACHE.get("line") or ""
        from .. import battle_sim
        army = {"miner": 21, "hog-rider": 11, "healer": 4}
        r = battle_sim.simulate(lay, army)
        if not r.get("ok"):
            line = _T("模拟：无法计算", "Sim: n/a")
        else:
            side_zh = {"west": "西", "east": "东", "north": "北", "south": "南", "inner": "内侧"}.get(r["side"], r["side"])
            line = _T("模拟：%s侧 路径%s 破墙%s 生存%.0f%% %d★" % (
                side_zh, r["path_len"], r["walls_to_break"], r["survival"] * 100, r["stars_estimate"]),
                "Sim: %s path %s walls %s surv %.0f%% %d★" % (
                r["side"], r["path_len"], r["walls_to_break"], r["survival"] * 100, r["stars_estimate"]))
        _SIM_CACHE.update({"key": key, "line": line})
        return line
    except Exception:
        return _T("模拟：无法计算", "Sim: n/a")


'''
    if anchor2 in t2:
        t2 = t2.replace(anchor2, add2 + anchor2, 1)
        # 在研究页对手行后插入显示
        old = '''    imgui.text_colored(imgui.ImVec4(*SUBTLE), _opponent_line(state))
    y += 20.0'''
        new = '''    imgui.text_colored(imgui.ImVec4(*SUBTLE), _opponent_line(state))
    y += 20.0
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text_colored(imgui.ImVec4(*SUBTLE), _battle_sim_line(state))
    y += 20.0'''
        if old in t2:
            t2 = t2.replace(old, new, 1)
            print("panel sim line inserted")
        else:
            print("panel insert anchor miss")
        open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    else:
        print("panel anchor miss")
else:
    print("panel sim already")
