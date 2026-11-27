# ClashLab v0.3.3（2026-11-27）

## 新增
- `clashlab/layout_grid.py` + `clashlab/layout_rules.py`：44×44 布局数据层 + 8 条可解释规则评分
- `tools/auto_report.py`：一条命令/批量出报告（含自动标定几何校验）
- `tools/self_check.py`：防守自检 + 推荐打法 + **进攻模拟**（启发式）
- `clashlab/battle_sim.py` + `tools/sim_attack.py`：简化战斗模拟（Dijkstra 寻路 + 防御 DPS 暴露 + 生存率/拆本时间/星级估算）
- 标注器 v3：四角吸附、箭线预览（A 键）、保存并出报告（R 键）
- ClashKing 免费端点集成：部落成员 TH（cached）、战争（type）、静态数据（max-level）
- 面板研究页：F6 识别后显示「部落 TH 分布」后缀

## 修复
- 双击启动可见（无参数 → PANEL，主屏可见）
- 繁体中文打包（zhconv 数据）
- PANEL 点击切换（去双鼠标通道）、研究/设置页重叠、单实例互斥

## 说明
- 战斗模拟为**启发式估算**（粗粒度兵种表 + 路径暴露），不是游戏真实引擎，仅用于相对比较。
- 非官方工具，请自行评估 ToS 风险。
