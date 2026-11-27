# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
st = os.path.join(BASE, "android", "assets", "annotate10_selftest.html")
if os.path.exists(st): os.remove(st); print("selftest removed")
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v30.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.3.0.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read(); md5 = hashlib.md5(data).hexdigest()
print("APK", len(data), "md5", md5)
lines = [
 "# ClashLab 标注 APK v0.3.0（20 张满防阵型 · 初学者版）",
 "",
 "## v0.3.0：已放建筑可以拖动调整",
 "- 点错位置不用删了重放：靠近已放建筑直接按住拖到正确格子",
 "- 保留 v0.2.9：显示「第 X/20 张 · 已完成 N」",
 "- 保留 v0.2.8：导出后自动跳下一张未标定图",
 "- 保留 v0.2.7：四角可拖出图片 + 拖到边缘自动平移",
 "- 保留：双击放大、类型列表收起、46 类全中文、沿用上张四角、全清空、导出 v2",
 "",
 "## 验证",
 "- 无头浏览器自测：放建筑 [18,18] → 拖动后 [23,22]，changed=true",
 "- 真机（v0.2.9）：进度 0→1、导出后跳第 2 张",
 "- 页面脚本 node --check 通过；APK " + format(len(data), ",") + " bytes md5 " + md5.upper(),
 "",
 "## 使用",
 "1. 点四角（可拖出图片；拖到屏幕边缘会自动平移）",
 "2. 双击放大；点「建筑：XX」选类型",
 "3. 点建筑中心；位置不准可直接按住拖到正确格子",
 "4. 「导出本张」自动跳下一张；标完 10 张「导出全部」发我 annot_all.json",
 "",
 "## 已知限制",
 "- Android 9 导出可能落 App 私有目录；Android 10+ 正常进「下载」",
]
open(os.path.join(BASE, "docs", "APK_20BASES.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("doc updated")
