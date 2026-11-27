# -*- coding: utf-8 -*-
import hashlib, os, shutil, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
subprocess.run([r"E:\leidian\LDPlayer9\adb.exe","-s","emulator-5554","shell","wm","size","1920x1080"],
               capture_output=True, text=True, timeout=60)
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v24.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.4.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read()
print("APK", os.path.basename(dst), len(data), "bytes md5", hashlib.md5(data).hexdigest())
BT = chr(96)
def c(s): return BT + s + BT
doc = "\n".join([
 "# ClashLab 标注 APK v0.2.4（20 张满防阵型 · 初学者版）",
 "",
 "## v0.2.4：屏幕留给阵型",
 "- **类型列表默认收起**：只保留一行「建筑：XX ▾」；点它才弹出选择面板，选完自动收起",
 "- 标定完成后**自动隐藏步骤条和提示**，图片区域进一步变大",
 "- 四角可拖动；＋/－/适应 与双指缩放、放大后单指平移（沿用 v0.2.3）",
 "- 46 类全中文、标点显示中文名、导出 v2（image_size + corners_norm）",
 "",
 "## 实测（LDPlayer Android 9，短屏 1920×864）",
 "- 标定后：步骤条隐藏 → 只剩一行类型按钮，图片更大",
 "- 点「建筑：防空」→ 面板展开（防御/核心/资源军队/陷阱）→ 点「散炮」→ 面板自动收起，按钮变「建筑：散炮」",
 "- 放置 2 栋 → 导出 JSON：散射炮 [18,18]、[22,27]，version=2 / image_size / corners_norm 齐全",
 "- 353 项测试 OK；JS 语法检查通过",
 "",
 "## 使用",
 "1. 安装 APK → 允许文件权限",
 "2. 点四个角（黄点可拖，＋/双指缩放）",
 "3. 点「建筑：防空 ▾」→ 选类型 → 面板自动收起 → 点建筑中心",
 "4. 标 10 张左右 →「导出全部」→ 发我 annot_all.json",
 "",
 "## 已知限制",
 "- Android 9 导出可能落 App 私有目录；Android 10+ 正常进「下载」。",
 "- 阵图来自第三方网站，版权归 Supercell/原站，仅本地学习用。",
])
open(os.path.join(BASE, "docs", "APK_20BASES.md"), "w", encoding="utf-8", newline="\n").write(doc + "\n")
print("doc updated")
