# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)

# ---------- A) runtime: 选对雷电实例（CoC 主窗） ----------
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
old = '''    main = [None]

    def _cb(h, _):
        if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
            main[0] = h

    win32gui.EnumWindows(_cb, None)
    if not main[0]:
        return None, None'''
new = '''    cands = []

    def _cb(h, _):
        if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
            cands.append((h, win32gui.GetWindowText(h) or ""))

    win32gui.EnumWindows(_cb, None)
    if not cands:
        return None, None
    # 多开时选对实例：标题恰为「雷电模拟器」优先（CoC），其次不带 -1/-2 后缀
    def _key(item):
        _h, title = item
        s = title.strip()
        if s == "雷电模拟器":
            return (0, len(s), _h)
        if "雷电" in s and not s.endswith(("-1", "-2", "-3", "-4")):
            return (1, len(s), _h)
        return (2, len(s), _h)
    cands.sort(key=_key)
    main = [cands[0][0]]'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("find_render_target fixed")
else:
    print("runtime anchor miss")

# ---------- B) pages: 语言按钮移到标签条右侧；删掉设置页重叠行 ----------
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()

# B1: 记录 root
if '_SESSION["_root"]' not in t2:
    t2 = t2.replace("    root = getattr(state, \"root\", \".\") or \".\"",
                    "    root = getattr(state, \"root\", \".\") or \".\"\n    _SESSION[\"_root\"] = root", 1)

# B2: 删除设置页语言块
old_lang = '''    # ---- 语言切换（简体中文 / English） ----
    lang.ensure_loaded(root)
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, "语言", "Language"))
    imgui.same_line(0.0, 10.0)
    _cur_lang = lang.get()
    if _btn("中文", (68.0, 24.0), kind="sec", active=_cur_lang in ("zh", "auto")):
        lang.set(root, "zh")
        ctx.log("UI language -> zh")
    imgui.same_line(0.0, 6.0)
    if _btn("繁體", (64.0, 24.0), kind="sec", active=_cur_lang == "zh-hant"):
        lang.set(root, "zh-hant")
        ctx.log("UI language -> zh-hant")
    imgui.same_line(0.0, 6.0)
    if _btn("English", (84.0, 24.0), kind="sec", active=_cur_lang == "en"):
        lang.set(root, "en")
        ctx.log("UI language -> en")
    imgui.same_line(0.0, 8.0)
    imgui.text_disabled(_L(ready, "（立即生效）", "(applies instantly)"))
    y += 30.0
'''
if old_lang in t2:
    t2 = t2.replace(old_lang, "", 1)
    print("settings language block removed")
else:
    print("lang block anchor miss")

# B3: tab row 右侧加语言按钮
old_tab = '''    avail_w = panel_w - 2 * PAD
    bw = (avail_w - GAP * (len(tabs) - 1)) / len(tabs)'''
new_tab = '''    LANGS = (("zh", "中"), ("zh-hant", "繁"), ("en", "EN"))
    LANG_W, LANG_GAP = 27.0, 4.0
    lang_reserve = len(LANGS) * LANG_W + (len(LANGS) - 1) * LANG_GAP + 8.0
    avail_w = panel_w - 2 * PAD - lang_reserve
    bw = (avail_w - GAP * (len(tabs) - 1)) / len(tabs)'''
if old_tab in t2:
    t2 = t2.replace(old_tab, new_tab, 1)
    print("tab width reserved")
old_loop = '''        if _btn(label, imgui.ImVec2(bw, 26.0),
                kind="amber" if active else "sec", key=f"tab_{key}"):
            ctx.set_page(key)'''
new_loop = '''        if _btn(label, imgui.ImVec2(bw, 26.0),
                kind="amber" if active else "sec", key=f"tab_{key}"):
            ctx.set_page(key)
    # 语言切换：标签条最右侧三个小钮（任何页都可见）
    _root = _SESSION.get("_root") or "."
    lang.ensure_loaded(_root)
    cur = lang.get()
    lx0 = px + panel_w - PAD - len(LANGS) * LANG_W - (len(LANGS) - 1) * LANG_GAP
    for i, (mode, lab) in enumerate(LANGS):
        imgui.set_cursor_screen_pos(imgui.ImVec2(lx0 + i * (LANG_W + LANG_GAP), 12.0))
        if _btn(lab, imgui.ImVec2(LANG_W, 26.0), kind="sec",
                active=(cur == mode or (mode == "zh" and cur == "auto")), key=f"lang_{mode}"):
            try:
                lang.set(_root, mode)
            except Exception:
                pass'''
if old_loop in t2:
    t2 = t2.replace(old_loop, new_loop, 1)
    print("lang buttons added to tab row")
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("pages patched")
