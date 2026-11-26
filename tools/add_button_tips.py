# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
pairs = [
 ('kind="pri", key="auto_capture"):',
  'kind="pri", key="auto_capture",\n                tip="抓取当前游戏画面并自动检测阵型（需要雷电窗口在前台）"):'),
 ('kind="pri", key="gen"):',
  'kind="pri", key="gen",\n                tip="需要先加载阵型/候选；LLM 模式还需要 API 配置"):'),
 ('imgui.ImVec2(110.0, SOURCE_H), kind="sec", key="run_study"):',
  'imgui.ImVec2(110.0, SOURCE_H), kind="sec", key="run_study",\n            tip="后台跑研究报告，完成后自动刷新面板"):'),
]
for a, b in pairs:
    if a in t:
        t = t.replace(a, b, 1)
        print("patched:", a[:40])
    else:
        print("miss:", a[:40])
open(p, "w", encoding="utf-8", newline="\n").write(t)
