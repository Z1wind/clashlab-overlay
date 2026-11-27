# -*- coding: utf-8 -*-
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + c("")
# 版本 0.3.6
p = os.path.join(BASE, "clashlab", "__init__.py")
t = open(p, encoding="utf-8").read()
t = re.sub(r'__version__ = "[^"]+"', '__version__ = "0.3.6"', t)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("version 0.3.6")
doc = ("# ClashLab v0.3.6（2026-11-27）\n\n"
       "## 新增\n"
       "- 一键战报：规则评分 + 修复建议 + 穿云箭 + 模拟 + 推荐配比 → HTML（面板「生成战报」按钮）\n"
       "- 兵种/法术真实图标补齐 39/39（含 root-rider、revive）\n"
       "- 1080p 战场侦察抓图流水线（战争地图 → 敌军 → 逐基地侦察截图，OCR 状态机 + 断线重连）\n"
       "- 面板无游戏时独立显示；标注器内置启动\n\n"
       "## 验证\n"
       "- 351 测试 OK；06 阵战报 98,453 bytes（A 70.0 / 预估 3 星）；侦察实测连抓 2 基地 1920x1080\n\n"
       "> 启发式分析，非游戏真实引擎；非官方工具，注意 ToS 风险。\n")
open(os.path.join(BASE, "docs", "RELEASE_v0.3.6.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("notes written")
