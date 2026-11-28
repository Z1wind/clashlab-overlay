# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist_exe", "ClashLabAnnotator.exe")
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v1.3.exe")
shutil.copyfile(src, dst)
data = open(dst, "rb").read(); md5 = hashlib.md5(data).hexdigest()
print("EXE", len(data), "md5", md5)
lines = [
 "# ClashLab 桌面标注器 v1.3（Windows EXE，无需 Python）",
 "",
 "## 新功能：自动预标注（AI）",
 "- 点完四个角后，点顶部「自动预标注」→ 模型自动放一批建筑（约 4 秒/张）",
 "- 你再删误报、补漏、改类型即可",
 "- 模型：门控(有没有建筑) + 36 类类型分类，ONNX CPU 推理，已打进 EXE",
 "",
 "## 模型效果（6 张好数据诚实留一验证）",
 "- 类型分类 top1 91.0% / top3 96.7%",
 "- 检测（预标注）：精度 71.5% / 召回 45.6% / 命中的类型准确率 87.4%",
 "- 实际单张 b03：识别 72 栋（GT 91），4.2 秒",
 "",
 "## 操作",
 "- 点击放四角/建筑；拖动平移；滚轮缩放；右键删建筑；Delete 删悬停；Ctrl+Z/Y 撤销重做",
 "- 「自动预标注」→ 确认替换 → 检查并修正",
 "",
 "## 保存",
 "导出到 Downloads\\ClashLab标注\\；「导出文件夹」可打开。",
 "",
 "## 验证",
 "- 打包环境 smoke：preannotate ok=true / n=72 / ms=4201；页面加载 20 图、保存 ok",
 "- 无 Python 环境可运行（PyInstaller 自带运行时）",
 "- 体积 106,311,382 bytes md5 " + md5.upper(),
]
open(os.path.join(BASE, "docs", "DESKTOP_APP.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("doc updated")
