# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## \U0001F504 2026-11-27 更新（本轮处理 STATUS 待办）\n\n"
       "### 已修 / 已验证\n"
       "- **P0-1 鼠标双通道**：PANEL 默认不再注入自喂鼠标（配置项 \x60panel_mouse_feed: true\x60 可恢复）；"
       "exe 实测点击四个标签页 → 研究/阵型/采集/设置 均正确切换（OCR 底栏验证）。\n"
       "- **P0-2 研究页重叠**：本地面板从 \x60content_top+56\x60 开始，刷新按钮/统计不再压引擎说明（截图 \x60out/live/research_final3.png\x60）。\n"
       "- **P1-4 HUD 穿云箭**：HUD 实机截图可见箭线+编号；日志 \x60hud-arrow: plan from=[6.24,44] to=[23,0] hits_drawn=4\x60。\n"
       "- **P1-5 异常窗口尺寸**：新增命名互斥 \x60ClashLabOverlaySingleton\x60；第二次启动实测日志 "
       "\x60another ClashLab overlay is already running; exit this instance\x60，窗口保持唯一 440×700。\n"
       "- **P2-7 调试行**：锚点坐标调试行默认隐藏（\x60config/overlay.json\x60 的 \x60show_anchor_debug: true\x60 才显示）。\n\n"
       "### 仍需人工 / 搁置\n"
       "- **P1-3 真实战图标注**：自动模板匹配不可用（误匹配严重），需用 \x60tools/annotate_web.py\x60 人工点 3–5 分钟；"
       "标注后一条命令可跑 \x60tools/enemy_pipeline.py\x60。\n"
       "- **P2-6 ClashKing token/布局库**：按要求本轮搁置。\n"
       "- **P2-8 检测器**：未启动（需单独立项）。\n")
if "2026-11-27 更新" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n\n" + add)
    print("STATUS updated")

p2 = os.path.join(BASE, "CHANGELOG.md")
t2 = open(p2, encoding="utf-8").read()
add2 = ("- 2026-11-27：修复 PANEL 点击不切换（去双鼠标通道）、研究页/设置页重叠、HUD 箭线绘制验证、"
        "单实例互斥、调试锚点默认隐藏。\n")
if "2026-11-27" not in t2:
    t2 = t2.replace("## v0.3.0 (unreleased)\n", "## v0.3.0 (unreleased)\n" + add2, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("CHANGELOG updated")
