# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 📱 2026-11-27：手机标注 APK v2 + v0.3.0 Release\n\n"
       "- APK：下载 " + "https://github.com/Z1wind/clashlab-overlay/releases/download/v0.3.0/ClashLabAnnotator.apk" + "\n"
       "- 已内置 3 张真实战图；流程：点 4 个网格角 → 选类型点建筑 → 导出 JSON（保存到 Download）\n"
       "- 实测：安装启动正常；导出 " + c("apk2_export.json") + " schema=" + c("clashlab-annotator-v2") + "，quad 4 点 + 1 栋 tile=[22,21]\n"
       "- Release v0.3.0 资产：ClashOverlay.exe（121,348,119 B）、ClashLabAnnotator.apk（10,032,264 B）、标注数据 zip（11,674,555 B）\n")
if "手机标注 APK v2" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("STATUS apk section added")
