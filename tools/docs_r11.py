# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
wl = "\n".join([
 "",
 "## 通宵轮次 11（2026-11-28 04:35-04:50）：尺度感知锚点校正（失败，记录）",
 "",
 "- 思路：按 footprint 推算立绘显示尺寸，只在旧标注预测位置 ±2 格搜索匹配，再 RANSAC 拟合 quad",
 "- 结果：82/86 个锚点被接受（阈值 0.80），RANSAC 内点 19，但叠加图显示红圈仍落在草地/墙上（out/layouts_src/scale_anchor_b01.png）",
 "- 结论：历史 5 张渲染图的标注本身不可信（类型与位置都可能错），无法通过几何校正救回；后续不要再在旧标注上做自动标注",
 "- 唯一可靠路线：用户用 APK v0.3.0 目视标注 → annot_all.json → tools/train_from_apk_export.py",
 "",
 "### 通宵收尾",
 "- 目标状态：APK v0.3.0（真机验证）、训练一条命令、CI/Release 完成；自动标注与 copy link 均证伪",
 "- 等用户：标注 10 张 + 政策改造批准",
 "",
])
open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n").write(wl)
print("worklog r11")
