# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
doc = ("# 检测器预研（C）结论：合成数据迁移失败（2026-11-27）\n\n"
       "## 做了什么\n"
       "- 合成检测数据集：" + c("tools/build_detect_dataset.py") + "，ClashKing 立绘贴草地背景，1500 train / 240 val，46 类（**排除 firespitter/wall**）\n"
       "- 训练：" + c("tools/centernet_fast.py") + "（纯 torch CenterNet-mini，320px，17 类关键防御，12 epoch，RTX 4060）\n"
       "- 推理：" + c("tools/eval_centernet_fast.py") + " 跑真实战图 " + c("out/live/enemy_scout_live.png") + "\n\n"
       "## 结果（真实数据）\n"
       "- 热图均值 **0.4915**、峰值 0.99 → 模型对整幅图都给出高置信，不是「检测到建筑」\n"
       "- 真实图上取 30 个框，**全部错位**：把左上角 UI（SHADOW 名字/资源）、按钮、岩石背景都框出来（见 " + c("out/live/detect_cf_eval.png") + "）\n"
       "- 训练集 val 上 heatmap focal loss 从 0.56 降到 0.537（几乎不降），说明合成图内也没学到稳定特征\n\n"
       "## 结论\n"
       "**预注册判据（真实图命中 ≥60%）不达标，检测器方向停止。**\n"
       "原因判断：合成背景与真实村庄域差距过大、立绘比例/遮挡/描边风格不同，加上 12 epoch 训练不足。\n\n"
       "## 若要继续（需要新输入）\n"
       "1. 真实截图 **人工框** 若干（≥200 栋）作训练/验证集——正好可用电脑标注器 " + c("tools/annotate_web.py") + " 产出；\n"
       "2. 或改「模板+几何约束」方案（已知阈值下不适用）；\n"
       "3. 不建议继续用纯合成数据硬训。\n")
open(os.path.join(BASE, "docs", "C_DETECT_SPIKE.md"), "w", encoding="utf-8", newline="\n").write(doc)

p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## 🔬 2026-11-27：检测器预研（C）已尝试并停止\n\n"
       "- 合成检测集 1500/240（排除 firespitter/wall）→ CenterNet-mini 训练 12 epoch → 真实战图推理\n"
       "- **结果：真实图 30 个框全部错位（UI/背景被当建筑），不达标** → 按预注册判据停止\n"
       "- 详见 " + c("docs/C_DETECT_SPIKE.md") + "；检测器可视化 " + c("out/live/detect_cf_eval.png") + "\n"
       "- 另外：firespitter 已在训练数据层排除（用户说明误标）；电脑标注器已在本机 8765 打开\n")
if "检测器预研（C）" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + add)
    print("STATUS updated")
