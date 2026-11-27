# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v29.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.9.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read(); md5 = hashlib.md5(data).hexdigest()
print("APK", len(data), "md5", md5)
lines = [
 "# ClashLab 标注 APK v0.2.9（20 张满防阵型 · 初学者版）",
 "",
 "## v0.2.9：显示总进度",
 "- 左上角显示「第 X/20 张 · 已完成 N」，一眼看到离 10 张还差多少",
 "- 保留 v0.2.8：导出后自动跳下一张未标定图",
 "- 保留 v0.2.7：四角可拖出图片 + 拖到边缘自动平移",
 "- 保留：双击放大、类型列表收起、46 类全中文、沿用上张四角、全清空、导出 v2",
 "",
 "## 验证",
 "- 真机（1920x864）：初始「第1/20张·已完成0」→ 标定后「已完成1」→ 导出后「第2/20张·已完成1」",
 "- 页面脚本 node --check 通过；APK " + format(len(data), ",") + " bytes md5 " + md5.upper(),
 "",
 "## 使用",
 "1. 点四角（可拖出图片；拖到屏幕边缘会自动平移）",
 "2. 双击放大；点「建筑：XX」选类型，选完自动收起",
 "3. 点建筑中心；点「导出本张」→ 自动跳下一张",
 "4. 标完 10 张左右 →「导出全部」→ 把 annot_all.json 发我",
 "",
 "## 已知限制",
 "- Android 9 导出可能落 App 私有目录；Android 10+ 正常进「下载」",
]
open(os.path.join(BASE, "docs", "APK_20BASES.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("doc updated")
