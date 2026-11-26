# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# keys: 每个动作补 en
p = os.path.join(BASE, "clashlab", "overlay", "keys.py")
t = open(p, encoding="utf-8").read()
pairs = [("切换面板", "Toggle panel"), ("采集一帧", "Capture frame"), ("Live 跟随", "Live follow"),
         ("重载情报", "Reload intel"), ("识别对手", "Identify opponent"), ("回 HUD", "Back to HUD")]
for zh, en in pairs:
    old = '"zh": "%s"' % zh
    if old in t and ('"zh": "%s", "en"' % zh) not in t:
        t = t.replace(old, old + ', "en": "%s"' % en, 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("keys en added")

# pages: 动作名 / 按钮 / 底部计数走 _L
p2 = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t2 = open(p2, encoding="utf-8").read()
if 'imgui.text(d["zh"])' in t2:
    t2 = t2.replace('imgui.text(d["zh"])',
                    'imgui.text(_L(ready, d["zh"], d.get("en") or d["zh"]))', 1)
    print("action label translated")
t2 = t2.replace('_btn(("取消" if cap_active else "改键") + f"##{aid}",',
                '_btn((_L(ready, "取消", "Cancel") if cap_active else _L(ready, "改键", "Rebind")) + f"##{aid}",')
t2 = t2.replace('_btn("清除" + f"##{aid}"', '_btn(_L(ready, "清除", "Clear") + f"##{aid}"')
t2 = t2.replace('_btn("恢复默认"', '_btn(_L(ready, "恢复默认", "Reset defaults")')
t2 = t2.replace('right = extra if extra else f"候选 {total} / 可见 {visible}"',
                'right = extra if extra else _L(ready, f"候选 {total} / 可见 {visible}", f"candidates {total} / visible {visible}")')
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("pages labels patched")
