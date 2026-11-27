# ClashLab v0.3.1（2026-11-27）

## 新增
- tools/report_one.py：一条命令从 annotated JSON 出「评分报告 + 俯视箭线图 + Markdown 摘要」
- docs/SAMPLE_REPORT.md：6 套 TH16 阵样例报告（评分 52.4–63.7，每阵 3 条箭线候选）

## 修复 / 变更
- PANEL 点击不切换（去双鼠标通道）、研究/设置页重叠、调试锚点默认隐藏、单实例互斥
- 手机标注 APK v2（内置 3 张真实战图；4 角标定 + 建筑点选 + JSON 导出）
- 训练数据排除 firespitter（用户误标）

## 研究结论（失败并停止）
- C 检测器：纯合成数据训练在真实战图 30 框全错 → docs/C_DETECT_SPIKE.md
- 自动标注：6 种标定法 + quad_model + 滑窗分类器均不可用 → docs/AUTO_ANNOTATE_FAIL.md

> 非官方工具；请自行评估 ToS 风险。
