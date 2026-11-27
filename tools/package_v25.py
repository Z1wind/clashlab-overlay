# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v25.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.5.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read()
print("APK", os.path.basename(dst), len(data), "bytes md5", hashlib.md5(data).hexdigest())
BT = chr(96)
def c(s): return BT + s + BT
doc = "\n".join([
 "# ClashLab 标注 APK v0.2.5（20 张满防阵型 · 初学者版）",
 "",
 "## v0.2.5 新增",
 "- **沿用上一张四角**：同一视角的连拍截图不用重复点四角",
 "- **双击放大**：双击图面在 1x / 2x 切换（配 ＋/－/适应 与双指缩放）",
 "- **全清空**：双段确认清空全部 20 张进度（在「清空」右侧）",
 "- 保留：四角可拖、类型列表收起为一行、选完自动收起、46 类全中文、标点中文名、导出 v2",
 "",
 "## 实测",
 "- 构建：ClashLabAnnotator_v25.apk 8,292,385 bytes md5 C68032E0DB48772ED175DABDA78D8D3A",
 "- 页面脚本 node --check 通过（16,955 bytes JS）",
 "",
 "## 使用",
 "1. 安装后首次允许文件权限",
 "2. 点四角（黄点可拖、双击放大）→ 选建筑 → 点中心",
 "3. 同视角多张可点「沿上张四角」",
 "4. 标 10 张左右 →「导出全部」→ 发我 annot_all.json",
 "",
 "## 已知限制",
 "- Android 9 导出可能落 App 私有目录；Android 10+ 正常进「下载」。",
 "- 阵图来自第三方网站（版权归原站/Supercell），仅本地学习用。",
])
open(os.path.join(BASE, "docs", "APK_20BASES.md"), "w", encoding="utf-8", newline="\n").write(doc + "\n")
print("doc updated")
