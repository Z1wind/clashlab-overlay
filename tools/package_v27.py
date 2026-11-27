# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v27.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.7.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read(); md5 = hashlib.md5(data).hexdigest()
print("APK", len(data), "md5", md5)
BT = chr(96)
doc = "\n".join([
 "# ClashLab 标注 APK v0.2.7（20 张满防阵型 · 初学者版）",
 "",
 "## v0.2.7：四角可拖出图片 + 边缘自动平移",
 "- 拖角到屏幕边缘时视图自动平移，四角可以无限往外拖（纵向不再受 2.7 格限制）",
 "- 角点归一化范围放宽到 -0.6 ~ 1.6；图片约 88% 舞台大小",
 "- 其余保留：双击放大、类型列表收起、46 类全中文、沿用上张四角、全清空、导出 v2",
 "",
 "## 验证",
 "- 无头浏览器自测（模拟拖到上边缘 60 次）：before=[0.3,0.3] after=[0.3,-0.6] ok=true",
 "- 自测（越界角点）：off=326,39 wh=1245x572 outside=[-0.2,0.5] ok=true",
 "- 页面脚本 node --check 通过；APK 8,300,644 bytes md5 " + md5.upper(),
 "",
 "## 使用",
 "1. 点四角；角在图外时就往屏幕边缘拖（到边缘会自动平移）",
 "2. 双击放大；类型列表点开选完自动收起",
 "3. 标完导出；下载目录取 annot_b01.json / annot_all.json",
 "",
 "## 已知限制",
 "- Android 9 导出可能落 App 私有目录；Android 10+ 正常进「下载」",
,
])
open(os.path.join(BASE, "docs", "APK_20BASES.md"), "w", encoding="utf-8", newline="\n").write(doc + "\n")
print("doc updated")
