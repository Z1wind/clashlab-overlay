# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
doc = ("# 真实战图「自动标注」尝试记录（2026-11-27，失败）\n\n"
       "目标：用户没空手标，尝试全自动生成 enemy_scout_live.png 的建筑坐标。\n\n"
       "## 尝试 1：自动标定（4 角）\n"
       "| 方法 | 结果 |\n|---|---|\n"
       "| clashlab.calib 草地轮廓 | 返回 4 点挤在一起（quad 各点相距 <150px），失败 |\n"
       "| 蓝墙连通域 minAreaRect | 只找到局部墙段（area 4233），失败 |\n"
       "| 蓝墙全像素 minAreaRect | 受 UI/水色污染，退化成整屏矩形，失败 |\n"
       "| 亮绿草地最大连通块 | 只抓到基地一角（95696px），失败 |\n"
       "| Hough 长直线拟合 | 只拟合到局部墙段，四角偏移出画面，失败 |\n"
       "| models/quad_model.pt（训练好的四角模型） | 输出整帧矩形（该模型是家园视角标定，侦察视角不适用） |\n"
       "| 人工目测四角 + 网格叠加 | 网格大致贴合（" + c("out/live/grid_manual2.png") + "），可作为近似标定 |\n\n"
       "## 尝试 2：滑窗分类检测\n"
       "- 用 " + c("models/synth_level.pt") + "（29 类，type_acc 0.979）在 44×44 网格上按 2/3/4 格足迹滑窗，"
       "warps 到 96×96 后分类，置信度 ≥0.90 取候选\n"
       "- **结果不可用**：分类器无「背景」类，对空白/墙/草地窗口也输出 0.9999 —— 如 " + c("town-hall 21,32 / 7,6 / 15,16 ...") + " 全是误报\n"
       "- 结论：没有真背景负样本，滑窗必假阳性；合成数据训练的闭集分类器不能直接当检测器\n\n"
       "## 因此\n"
       "- 真实阵的评分/穿云箭分析**必须**有至少近似准确的建筑坐标（TH/鹰/吹风/防空是硬依赖）\n"
       "- 当前唯一可靠路径：标注器点 4 个角 + 10–20 栋（约 2–3 分钟）\n"
       "- 网页标注器已在本机运行：" + c("http://127.0.0.1:8765") + "（" + c("tools/annotate_web.py") + "），\n"
       "  导出文件走 " + c("tools/enemy_pipeline.py") + " 即可出评分/箭线\n")
open(os.path.join(BASE, "docs", "AUTO_ANNOTATE_FAIL.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("doc written")

p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 🧪 2026-11-27：真实战图自动标注尝试（失败，见 AUTO_ANNOTATE_FAIL.md）\n\n"
       "- 6 种自动标定方法 + quad_model + 滑窗分类器全部不可用；滑窗假阳性率 100%（无背景类）\n"
       "- 结论：真实阵分析必须人工点 4 角 + 10–20 栋（约 2–3 分钟）；标注器已在 8765 运行\n")
if "自动标注尝试" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("STATUS updated")
