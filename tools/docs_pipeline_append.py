# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
with open(os.path.join(BASE, "docs", "TRAIN_RESULT_20261128.md"), "a", encoding="utf-8", newline="\n") as f:
    f.write("\n".join([
        "",
        "## 后续训练（同日 16:40-17:00）",
        "",
        "### 类型分类器升级（6 张好数据留一）",
        "- 112px/26 轮：top1 88.2% / top3 94.8%",
        "- 112px/40 轮：top1 91.0% / top3 96.7%（当前最佳，models/apk_type_cls_s112e40.pt）",
        "- 128px/35 轮：top1 89.5% / top3 95.6%",
        "",
        "### 自动找位置（新方向）",
        "- 单阶段 39 类扫描器：prec 32.5% / recall 64.1% / F1 0.42 / 类型 83.1%",
        "- 两阶段门控（bg vs 建筑）：prec 61.1% / recall 73.7% / F1 0.645",
        "- 完整流水线（每折重训门控+类型，诚实 CV）：prec 71.5% / recall 45.6% / F1 0.545 / 类型 87.4%",
        "- 结论：预标注已有可用雏形（高精度低召回），下一步导出 ONNX 集成进桌面版「一键预标注」",
        "",
    ]))
print("docs appended")
