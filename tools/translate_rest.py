# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()

# _T helper（不依赖 ready，任何函数都能用）
if "def _T(" not in t:
    t = t.replace("def _panel_origin():", '''def _T(zh, en):
    """无 ready 参数处的简/繁/英切换。"""
    from . import lang
    mode = lang.get()
    if mode == "en":
        return en
    if mode == "zh-hant":
        return lang.to_hant(zh)
    return zh


def _panel_origin():''', 1)
    print("_T added")

PAIRS = [
 ("面板位置（外置窗口）", "Panel position (external window)"),
 ("重新对位", "Recalibrate"),
 ("已采用 view_quads.json 校准标志", "Calibration flag from view_quads.json"),
 ("HUD 显示「视角可能已变」角标", "Show 'view may have changed' badge on HUD"),
 ("贴合偏移（保存由运行时写 config）", "Fit offset (runtime saves to config)"),
 ("退出覆盖层", "Exit overlay"),
 ("已保存 overlay_keys.json", "Saved overlay_keys.json"),
 ("默认键已避开雷电热键（F8/F9/F11）", "Default keys avoid LDPlayer hotkeys (F8/F9/F11)"),
 ("快捷键绑定", "Hotkeys"),
 ("实测锚点", "Verified anchors"),
 ("其余 7 条见 config/anchors.json", "Other 7 anchors: config/anchors.json"),
 ("条（灰=未验证）", " (grey = unverified)"),
 ("面板", "Panel"),
 ("实时=", "Live="),
]
for zh, en in PAIRS:
    needle = '"' + zh + '"'
    if needle in t:
        t = t.replace(needle, "_T(%s, %s)" % (needle, '"' + en + '"'), 1)
        print("translated:", zh)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("done")
