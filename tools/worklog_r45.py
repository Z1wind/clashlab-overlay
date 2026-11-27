# -*- coding: utf-8 -*-
import os
BASE = "C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat"
wl = "\n".join([
 "",
 "## 通宵轮次 4-5（2026-11-28 02:40-03:10）",
 "",
 "### APK v0.2.6：四角可以拖出图片边界",
 "- 用户反馈：APK 不能像最初 HTML 那样把角拉到截图外",
 "- 根因：角点归一化坐标被 clamp 在 0..1",
 "- 修复：画布按舞台比例留 6% 边距，角点允许 -0.25..1.25；fitCanvas 改为舞台相对",
 "- 图片保持约 88% 舞台大小（横向可伸出约 11 格，纵向约 2.7 格）",
 "- 无头浏览器自测：off=326,39 wh=1245x572 outside=[-0.2,0.5] ok=true",
 "- 模拟器真机导出：corners_norm 含 -0.016 / 1.039，HAS_OUTSIDE=True",
 "- 产物：dist/ClashLabAnnotator_20bases_v0.2.6.apk 8,300,644 bytes md5 FEEEAD7CC47722E1F087DF35075666CB",
 "- Release v0.3.7 资产已替换并校验 md5；提交 ef0b608",
 "",
 "### 数据集流水线兼容外部角点",
 "- tools/apk_export_to_dataset.py 支持 corners_norm 为负/超过 1（warpPerspective 采样边界外为黑）",
 "- tests/test_apk_export_dataset.py 新增：外部角点不崩溃、bundle 导出解析；3 项测试 OK",
 "",
])
open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n").write(wl)
print("worklog appended")
