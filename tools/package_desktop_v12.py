# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist_exe", "ClashLabAnnotator.exe")
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v1.2.exe")
shutil.copyfile(src, dst)
data = open(dst, "rb").read(); md5 = hashlib.md5(data).hexdigest()
print("EXE", len(data), "md5", md5)
lines = [
 "# ClashLab 桌面标注器 v1.2（Windows EXE，无需 Python）",
 "",
 "## 本版修复（重要）",
 "- **没法标点** 的根因：为做左键拖动平移，把每次点击也标记成平移，导致单击不触发放置",
 "- 修复：拖动距离超过 6px 才进入平移；原地单击 = 点四角 / 放建筑",
 "- 真实鼠标事件自测：点击放置四角 corners=4、放建筑 bld=1、左键拖动 pan=(120,60) 平移生效",
 "",
 "## 运行",
 "双击 ClashLabAnnotator_Desktop_v1.2.exe（单文件约 20MB）；不需要 Python（已用剥离 PATH 的环境实测退出码 0）。",
 "",
 "## 电脑操作习惯",
 "- 滚轮缩放（指针为中心）、左键拖空白平移（拖动超过 6px 才算拖）",
 "- 左键单击：点四角 / 放建筑",
 "- 按住角点/建筑拖动：微调、挪位",
 "- 右键建筑删除；Delete 删除悬停；Esc 收起类型面板",
 "- Ctrl+Z 撤销 / Ctrl+Y 重做 / Ctrl+S 导出 / ← → 切图",
 "- 底部显示「格 x,y | 缩放 %」",
 "",
 "## 保存",
 "导出直接写 用户\\Downloads\\ClashLab标注\\；右下「导出文件夹」可直接打开。",
 "",
 "## 验证",
 "- 无 Python：PATH 仅 C:\\Windows，EXE 退出码 0，加载 20 图，保存 smoke_test_5.json（ok:true）",
 "- 正常启动：窗口标题 ClashLab 阵型标注（桌面版 v1.2）",
 "- 点击/拖动自测：corners=4 bld=1 grid=11675 panned=true",
]
open(os.path.join(BASE, "docs", "DESKTOP_APP.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("doc updated")
