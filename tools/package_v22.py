# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = r"E:\ClashLab\android\dist\ClashLabAnnotator_v22.apk"
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.2.apk")
shutil.copyfile(src, dst)
data = open(dst, "rb").read()
print("APK", os.path.basename(dst), len(data), "bytes md5", hashlib.md5(data).hexdigest())
BT = chr(96)
def c(s): return BT + s + BT
doc = "\n".join([
 "# ClashLab 标注 APK v0.2.2（20 张满防阵型 · 初学者版）",
 "",
 "## 更新（v0.2.1/0.2.2）",
 "- **四角可拖动**：点完 4 个角后，按住黄点拖到真正角上（解决死角/点不到）",
 "- **建筑类型补全 + 全中文**：防御 18 类 / 核心 5 类 / 资源军队 15 类 / 陷阱 8 类，共 46 类；按钮显示「简称 · 中文全名」",
 "- **标点带中文名**：放置后黄圈旁显示中文（可「名称:开/关」切换）",
 "- 导出格式 v2：包含 " + c("image_size") + " 与 " + c("corners_norm") + "，可直接转训练集",
 "- 「重设四角」按钮；双段确认清空；首启教程自动弹出",
 "",
 "## 安装",
 "1. 安装 " + c("ClashLabAnnotator_20bases_v0.2.2.apk") + "（未知来源允许）。",
 "2. 首次弹权限点「允许」。",
 "3. 教程 → 点四角（可拖动微调）→ 选建筑 → 点建筑中心。",
 "4. 「导出全部」→ JSON（Android 10+ 在「下载」；Android 9 在 App 私有目录，提示会说明）。",
 "",
 "## 实测（LDPlayer Android 9 1920x1080）",
 "- 安装 Success；首启教程自动弹出；四角拖动实测：角点位移 (+40,+40) 写入 JSON",
 "- 中文标点与「名称开关」正常；点已标建筑删除、撤销、双段清空正常",
 "- 导出 v2：version=2 / image_size=[1600,735] / corners_norm 4 点 / buildings 带中文 name",
 "- 转换脚本 " + c("tools/apk_export_to_dataset.py") + " 实测：导出 → 2 张 96×96 训练裁剪",
 "- 353 项测试 OK；logcat 无 JS/崩溃错误",
 "",
 "## 已知限制",
 "- 旧 Android(9) 导出可能落 App 私有目录（文件管理 Android/data/com.clashlab.annotator/files/Downloads）；Android 10+ 正常进「下载」。",
 "- 阵图来自第三方网站（版权归 Supercell/原站），仅本地学习用；图片带原站水印。",
 "- 自动类型识别仍需累计标注后训练。",
])
open(os.path.join(BASE, "docs", "APK_20BASES.md"), "w", encoding="utf-8", newline="\n").write(doc + "\n")
print("doc updated")
