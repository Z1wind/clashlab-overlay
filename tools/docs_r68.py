# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
wl = "\n".join([
 "",
 "## 通宵轮次 6-8（2026-11-28 03:10-04:05）",
 "",
 "### APK v0.2.7 / v0.2.8",
 "- v0.2.7：拖角到屏幕边缘自动平移（真机实测拖到顶边后 corners_norm[0]=[0.024,-0.6]，MIN_Y=-0.6）",
 "- v0.2.8：导出成功后自动跳到下一张未标定的图（真机 1/20 -> 2/20）",
 "- 当前产物：dist/ClashLabAnnotator_20bases_v0.2.8.apk 8,308,903 bytes md5 A1DE12AED7930E51CBA511BEF6DB9C69",
 "",
 "### 训练流水线（一条命令）",
 "- 新增 tools/train_from_apk_export.py：APK 导出 JSON -> crops -> 训练 CNN -> 留一基 top1/top3 -> 保存 models/apk_type_cls.pt",
 "- 烟测：01_annotated 转 v2 导出，86 crops / 31 类，训练+保存通过（单基无法留一评估，多基后自动 CV）",
 "",
 "### 历史结论去重（重要）",
 "- docs/BASELINK_RESEARCH.md 早已写明 copy link 不可离线解码（24B 服务端引用）——本轮 r1 又验证了一次，后续不要再试",
 "- docs/AUTO_ANNOTATE_FAIL.md 已记录自动标注失败（无背景类、滑窗假阳性），本次模板匹配 TP=0 再次印证",
 "",
])
open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n").write(wl)
brief = "\n".join([
 "# 早晨简报（2026-11-28）",
 "",
 "## 现在可以直接用",
 "1. 装 dist/ClashLabAnnotator_20bases_v0.2.8.apk（md5 A1DE12AED7930E51CBA511BEF6DB9C69）",
 "2. 点四角，可拖到图片外（拖到屏幕边缘会自动平移）",
 "3. 双击放大、点「建筑：XX」选类型、点建筑中心",
 "4. 「导出本张」自动跳下一张；标完 10 张点「导出全部」",
 "5. 把 annot_all.json 发我，我跑一条命令训练：",
 "   python tools/train_from_apk_export.py --export annot_all.json --epochs 12",
 "",
 "## 通宵完成清单",
 "- copy link 解码：确认不可行（且历史文档早有结论）",
 "- 自动标注：模板匹配/格点分类器均证伪（与历史记录一致）",
 "- APK：v0.2.6 四角可拖出图片、v0.2.7 边缘自动平移、v0.2.8 导出自动跳下一张（均真机验证）",
 "- 工程：可移植构建脚本 + GitHub Actions 自动出包 + Release v0.3.7 + 训练一条命令",
 "",
 "## 等你",
 "- 政策风险改造是否启动（删 ADB 自动侦察 / 覆盖层降级 / 改名 / 去 Supercell 素材）",
 "- 标注目标是否仍按先 10 张冲阶段 A",
])
open(os.path.join(BASE, "docs", "MORNING_BRIEF.md"), "w", encoding="utf-8", newline="\n").write(brief)
print("docs updated")
