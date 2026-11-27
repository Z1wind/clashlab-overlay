# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
lines = [
 "",
 "## 2026-11-27 A：标注器内置服务 + 无游戏独立面板",
 "",
 "- 新增 " + c("clashlab/annotator.py") + "：幂等 start_server / is_running / ensure_running / stop_server；tools/annotate_web.py 变薄 CLI",
 "- 面板设置页新增「启动标注器」按钮：未运行则后台线程拉起并打开浏览器",
 "- 无渲染目标时 PANEL 独立显示（主屏右侧 440x700），不再只显示小横幅",
 "- 实机验证：面板 (1472,30,440x700) -> OCR 定位按钮点击 -> 日志 annotator started -> HTTP 200（9542 bytes）",
 "- 测试：新增 annotator_service 4 项，全量 344 OK",
]
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
if "标注器内置服务" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + "\n".join(lines) + "\n")
    print("STATUS updated")
