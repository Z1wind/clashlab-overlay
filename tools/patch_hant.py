# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# ---------- lang.py：zh-hant ----------
p = os.path.join(BASE, "clashlab", "overlay", "lang.py")
t = open(p, encoding="utf-8").read()
t = t.replace('_MODES = ("auto", "zh", "en")', '_MODES = ("auto", "zh", "zh-hant", "en")')
if "def to_hant" not in t:
    t = t.replace('''def label(zh, en):''',
'''_HANT_CACHE = {}


def to_hant(text):
    """懒加载 zhconv 做简->繁。zhconv 不可用时原样返回。"""
    s = str(text or "")
    hit = _HANT_CACHE.get(s)
    if hit is not None:
        return hit
    try:
        import zhconv
        out = zhconv.convert(s, "zh-hant")
    except Exception:
        out = s
    _HANT_CACHE[s] = out
    return out


def label(zh, en):''')
    t = t.replace('''    if _current == "en":
        return en
    return zh''',
'''    if _current == "en":
        return en
    if _current == "zh-hant":
        return to_hant(zh)
    return zh''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("lang zh-hant patched")

# ---------- pages._L + 设置页第三按钮 ----------
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace('''def _L(ready, zh, en):
    from . import lang
    mode = lang.get()
    if mode == "en":
        return en
    if mode == "zh":
        return zh
    return en if not ready else zh''',
'''def _L(ready, zh, en):
    from . import lang
    mode = lang.get()
    if mode == "en":
        return en
    if mode == "zh-hant":
        return lang.to_hant(zh)
    if mode == "zh":
        return zh
    return en if not ready else zh''')
old_btn = '''    imgui.same_line(0.0, 6.0)
    if _btn("English", (84.0, 24.0), kind="sec", active=_cur_lang == "en"):'''
new_btn = '''    imgui.same_line(0.0, 6.0)
    if _btn("繁體", (64.0, 24.0), kind="sec", active=_cur_lang == "zh-hant"):
        lang.set(root, "zh-hant")
        ctx.log("UI language -> zh-hant")
    imgui.same_line(0.0, 6.0)
    if _btn("English", (84.0, 24.0), kind="sec", active=_cur_lang == "en"):'''
if old_btn in t2:
    t2 = t2.replace(old_btn, new_btn, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("settings hant button added")

# ---------- CLI choices ----------
for fn in ("run_overlay.py", "overlay_exe_main.py"):
    p3 = os.path.join(BASE, fn)
    s = open(p3, encoding="utf-8").read()
    s = s.replace('choices=["auto", "zh", "en"]', 'choices=["auto", "zh", "zh-hant", "en"]')
    open(p3, "w", encoding="utf-8", newline="\n").write(s)
print("cli choices updated")

# ---------- 测试补充 ----------
p4 = os.path.join(BASE, "tests", "test_lang.py")
t4 = open(p4, encoding="utf-8").read()
if "test_hant" not in t4:
    t4 = t4.replace('''    def test_pages_L_respects_mode(self):''',
'''    def test_hant_label(self):
        self.lang._current = "zh-hant"
        out = self.lang.label("设置", "Settings")
        self.assertIn("設", out)

    def test_pages_L_hant(self):
        from clashlab.overlay import pages, lang
        lang._current = "zh-hant"
        self.assertEqual(pages._L(True, "设置", "setting"), lang.to_hant("设置"))
        lang._current = "auto"

    def test_pages_L_respects_mode(self):''')
    open(p4, "w", encoding="utf-8", newline="\n").write(t4)
    print("hant tests added")
