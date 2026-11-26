# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()

# research local 页下移，避开引擎说明
t = t.replace("def _draw_local(ctx, state, root, ready, panel_w, px, H):\n    \"\"\"本地模式：列出本地规则引擎算出的重要防御，点按钮切换 HUD 聚焦。\"\"\"\n    y = _content_top(root)",
              "def _draw_local(ctx, state, root, ready, panel_w, px, H):\n    \"\"\"本地模式：列出本地规则引擎算出的重要防御，点按钮切换 HUD 聚焦。\"\"\"\n    y = _content_top(root) + 18.0", 1)

PAIRS = [
 ("推荐：无数据", "Recommendation: no data"),
 ("建筑：无数据", "Buildings: no data"),
 ("推演：无数据", "Simulation: no data"),
 ("对手：未识别（F6）", "Opponent: unknown (F6)"),
 ("距边未知", "edge: unknown"),
]
for zh, en in PAIRS:
    # 仅替换作为完整字符串字面量出现的情况
    needle = '"' + zh + '"'
    if needle in t:
        t = t.replace(needle, '_T(%s, %s)' % (needle, '"' + en + '"'))
        print("translated:", zh)
# 聚焦行
t = t.replace('f"聚焦 {cur[\'name\']} · {cur[\'dps\']} dps · {edge}"',
              '_L(ready, f"聚焦 {cur[\'name\']} · {cur[\'dps\']} dps · {edge}",\n                              f"Focus {cur[\'name\']} · {cur[\'dps\']} dps · {edge}")')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("done")
