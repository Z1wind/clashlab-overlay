# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
doc = ("# 真实域样本实验结论（2026-11-27）\n\n"
       "## 做法\n"
       "- 从 clashofclans-layouts.com 下载 5 张 TH16 原始图纸（2622×1206，与标注 quad 精确匹配）" + c("tools/download_layout_originals.py") + "\n"
       "- 用「标注 tile + quad」生成真实图纸裁剪：383 建筑正样本（带类型，32 类）+ 2000 背景负样本，" + c("datasets/real_layout/") + "（2,383×96×96）\n"
       "- 留出 defence_17 作为验证阵（train 4 阵 / val 1 阵）\n\n"
       "## 实测结果（诚实）\n"
       "| 模型 | 指标 | 结果 |\n|---|---|---|\n"
       "| 类型分类器（合成训练）| 真实图纸 top1/top3 | **7.9% / 17.5%**（n=63 可映射类型）|\n"
       "| 类型分类器（真实微调 8 epoch）| 真实图纸 top1/top3 | **14.3% / 33.3%**（仍不可用）|\n"
       "| 建筑门控（合成+背景训练）| 留出阵 precision/recall | 0.0 / **0.0**（tp=0, fn=76）|\n"
       "| 建筑门控（真实微调）| 留出阵 | 0.0 / 0.0（collapse 全负）|\n\n"
       "## 结论（关键）\n"
       "1. **布局网站的图纸不是游戏截图域**：扁平等距绘制 vs 游戏等距渲染，模型跨域完全失效（门控召回 0）\n"
       "2. 合成立绘训练的模型也不能直接用于真实截图类型识别（top1 7.9%）\n"
       "3. 因此「用布局图生成训练样本」这条捷径不可行；要提升 B，必须用**真实游戏截图 + 标注**\n"
       "4. 当前可用的路径仍是：门控只给「建筑位置候选」（截图域实测可用），类型由人工点选\n\n"
       "## 产物（保留供参考）\n"
       "- " + c("models/real_type.pt") + "（真实图纸微调，14.3% top1，实验性，勿用于生产）\n"
       "- " + c("models/building_gate_real.pt") + "（在图纸域失效，保留作对照）\n"
       "- " + c("models/real_finetune_metrics.json") + "（上述指标原始记录）\n"
       "- " + c("out/labels/montage_1..3.png") + "（71 个截图候选裁剪，供人工/AI 标注；分辨率有限）\n\n"
       "## 下一步建议\n"
       "1. 用更高分辨率截图（1080p/2K）重截，我可以直接看图标注建筑类型（96px 裁剪足够清晰）\n"
       "2. 或你标 2–3 个阵（现有标注器），我用真实截图域样本微调门控/类型\n"
       "3. 在此之前，自动候选只保留位置模式（已上线）\n")
open(os.path.join(BASE, "docs", "REAL_DOMAIN_FINDINGS.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("doc written")
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
if "真实域样本实验" not in t:
    t = t.rstrip() + "\n\n## 2026-11-27 真实域样本实验（失败结论）\n\n- 图纸生成 2383 张带类型样本；类型 top1 7.9%→14.3%，门控留出阵召回 0% → 布局图纸域不可迁移；详见 docs/REAL_DOMAIN_FINDINGS.md\n"
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("STATUS updated")
