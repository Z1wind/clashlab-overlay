# -*- coding: utf-8 -*-
import hashlib, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "dist_exe", "ClashLabAnnotator.exe")
dst = os.path.join(BASE, "dist", "ClashLabAnnotator_Desktop_v1.5.exe")
shutil.copyfile(src, dst)
data = open(dst, "rb").read(); md5 = hashlib.md5(data).hexdigest()
print("EXE", len(data), "md5", md5)
lines = [
 "# ClashLab 桌面标注器 v1.5（Windows EXE，无需 Python）",
 "",
 "## v1.5：混合预标注（门控 + 特征比对）",
 "- 你的「特征比对」思路落地：CNN 门控找建筑 + embedding(ArcFace) 最近邻认类型/背景校验",
 "- 8 张留一验证：P62.3% / R71.0% / F1 0.658 / 命中类型 91.8%",
 "- 对比旧版（软分类）：P70.4 / R53.2 / F1 .597 / 类型 83.1% → 召回 +18pt、类型 +9pt",
 "- 类型分类器：9 张…（8 张 CV top1 95.4% / top3 98.2%）",
 "- EXE " + format(len(data), ",") + " bytes，模型内置，无需 Python",
 "",
 "## 用法",
 "点四角 → 顶部「自动预标注」（约 4 秒）→ 自动放 ~70 栋 → 右键删误报、补漏 → 导出",
 "",
 "## 验证",
 "- 打包环境 smoke2：ok=true / n=72 / ms=3759（混合模型 ONNX 推理）",
 "- 页面 smoke：20 图加载、保存 ok",
]
open(os.path.join(BASE, "docs", "DESKTOP_APP.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("doc updated")
