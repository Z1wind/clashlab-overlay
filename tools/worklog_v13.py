# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
with open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n") as f:
    f.write("\n".join([
        "",
        "## 训练与预标注交付（2026-11-28 16:30-17:30）",
        "- 类型分类器升级：112px/40轮 CV top1 91.0% / top3 96.7%（models/apk_type_cls_s112e40.pt）",
        "- 自动找位置：单阶段扫描器 P32.5/R64.1/F1 .42 → 两阶段门控 P61.1/R73.7/F1 .645",
        "- 完整流水线诚实 CV：P71.5 / R45.6 / type_acc 87.4%；ONNX 推理 2.3-4.2s/张",
        "- 桌面版 v1.3：内置 ONNX 模型 + 「自动预标注」按钮；打包环境 smoke n=72 / 4201ms",
        "- 产物：dist/ClashLabAnnotator_Desktop_v1.3.exe 106,311,382 bytes md5 C5A1985C67A688404D467EFE68F659AF",
        "- Release v0.3.7 资产已上传并校验；git 提交 72e7afd（清理 dist_exe/build_exe 误入库）",
        "",
    ]))
print("worklog updated")
