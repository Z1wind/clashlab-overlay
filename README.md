<div align="center">

# ClashLab · 部落冲突战术辅助覆盖层

**进程外 · 零注入 · 只看画面** —— 把「侦察截图 → 地图标定 → 布局评分 → 赛前简报 → 战术标注」做成一条可复现的流水线。

[![License: MIT](https://img.shields.io/badge/license-MIT-3da639.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-3776ab.svg)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4.svg)]()
[![Tests](https://img.shields.io/badge/tests-270%20passing-brightgreen.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-ff69b4.svg)](CONTRIBUTING.md)

[中文](README.md) · [English](README.en.md)

</div>

> **100% 开源**：代码、数据、文档全部在本仓库，MIT 许可，无遥测、无服务器、无账号、无游戏注入。

![PANEL 面板](docs/screenshots/panel.png)

## ✨ 这是什么

一个贴在雷电模拟器上的半透明覆盖层：读游戏画面 → 算 → 画标注。它不注入游戏、不读内存、不连游戏服务器，所有结论都来自屏幕像素 + 本地计算。

| 能力 | 说明 |
|---|---|
| 🖥 **HUD / PANEL 双模式** | HUD 在画面上标注（鼠标穿透）；PANEL 右侧 440 宽面板（研究/阵型/采集/设置） |
| 🎯 **地图标定** | 44×44 网格 DLT 单应，窗口尺寸变化 >10% 自动重标定 |
| 📊 **布局防守评分** | 7 指标加权 → 0–100 + S/A/B/C/D/F，弱点带方位 |
| 🧠 **布局弱点 → 战术** | 大本营偏心 / 对空 / 对地覆盖率自动进简报与 LLM 提示 |
| 🏹 **女王穿云箭战术图** | 撒兵环 + 箭线 + 被穿防空编号 + 阶段色条，输出 PNG |
| 🗺 **2D 推演** | 候选落点与预估摧毁率，接入面板（带缓存） |
| 🧾 **赛前简报** | 规则引擎生成，可选大模型复核（只依据已知/未知，不猜） |

## 🖼 截图

| 战术图 | 面板评分 |
|---|---|
| ![穿云箭](docs/screenshots/giant_arrow.jpg) | ![面板](docs/screenshots/panel.png) |

## 🚀 快速开始

```powershell
git clone https://github.com/<your-name>/clashlab-overlay.git
cd clashlab-overlay
python -m pip install -r requirements.txt

# 可见覆盖层（8 秒自退，便于验证）
python run_overlay.py --show --mode HUD --always-on-top --run-seconds 8

# 单元测试（应 86 项全绿）
python -m unittest discover -s tests
```

详细步骤见 [docs/教程.md](docs/教程.md)（环境 / 模拟器 / 模式 / 评分 / 简报 / 打包 / FAQ）。

## 🧩 架构

```text
┌──────────────┐   PrintWindow    ┌───────────────┐
│ 雷电模拟器    │ ───────────────▶ │ 抓帧 + 标定     │
│ 1280×720     │                  │ 44×44 网格单应  │
└──────────────┘                  └──────┬────────┘
                                        ▼
                 ┌────────────────────────────────────┐
                 │ 分析层：layout_score / analysis / sim │
                 │ 评分 S–F · 弱点 · 撒兵环 · 推演        │
                 └──────────────┬─────────────────────┘
                                ▼
        ┌──────────────────────────────────────────┐
        │ 呈现层：ImGui 覆盖层 HUD / PANEL           │
        │ 战术图 PNG · 赛前简报 · LLM 复核（可选）    │
        └──────────────────────────────────────────┘
```

## 📊 评分指标（权重合计 13）

| 指标 | 权重 | 可信度 |
|---|---|---|
| 大本营保护 | 3 | ✅ |
| 资源仓保护 | 2 | ✅（纯防御标注时为 N/A） |
| 对空覆盖 | 2 | ✅ |
| 对地覆盖 | 2 | ✅ |
| 隔间质量 | 2 | ⚠️ 墙数据未补全，暂 N/A |
| 墙体效率 | 1 | ⚠️ 同上 |
| 入口防守 | 1 | ✅ |

## 🆕 最近（2026-11-26）

- **对手识别**：截图 OCR 名字/部落 → ClashKing API 自动查 TH/部落战成员（`docs/OCR_OPPONENT.md`）；
- **等级体系**：建筑/兵种/英雄等级进推演（低配兵摧毁率 18.95% → 8.55%），TH 满级自动回填；
- **兵棋推演 + 撒兵线**：确定性 tick + Monte Carlo；放兵线实测摧毁率 17.9% → 24.7%；
- **Android 标注 App**：离线补标 6 阵，导出 JSON 回传（`docs/ANDROID_APP.md`）。

- **战术知识库**：特斯拉默认隐身且 DPS 低（TH16 130 vs 防空 330），穿云箭优先串吹风机+防空火箭，图例/评分自动提醒（`docs/TACTICS.md`）。

- **实机测试**：雷电窗口只读截图 + OCR + API（发现同名歧义并加 #TAG 优先解析），见 `docs/LIVE_TEST.md`。

- **中英文界面切换**：设置页 [中文]/[English] 一键切换，或 `--lang en` / `CLASHLAB_LANG=en`（docs/I18N.md）。

- **英雄落点→穿云箭方向**：按「最近建筑中心」推箭线，并做 ±0.5 格落点敏感性测试（stable/flips）；`tools/arrow_placement_cli.py`。
- **三语界面**：设置页 [中文] [繁體] [English]，或 `--lang zh-hant`。

- **批量压测**：98 例（真实 6 阵 × 6 变体 + 20 生成阵）跑穿云箭选线/落点敏感性，仅 26% 落点稳定、13 例目标翻转（`docs/ARROW_BATCH.md`）。

- **真实战图实机验证**：部落战侦察屏 OCR+API 一次成功（SHADOW TH17 / #PLVYQ0G2U），见 `docs/LIVE_TEST.md`。

- **本地网页标注器**：`python tools/annotate_web.py --image out/live/enemy_scout_live.png` → 浏览器点 4 角 + 建筑 → 导出 annotated JSON（docs/ANNOTATE_WEB.md）。
- **敌方阵型流水线**：`python tools/enemy_pipeline.py --layout X_annotated.json` → 评分/弱点 + 穿云箭最优线 + 落点敏感性，一次输出。

- 下载 / 备份：[Releases](https://github.com/Z1wind/clashlab-overlay/releases)（最新 `backup-2026-11-26`：exe + 标注数据 zip）。

## 🗺 路线图

- [x] 覆盖层 HUD/PANEL + 自动重标定
- [x] 布局评分（0–100 / S–F）与弱点归因
- [x] 布局弱点接入简报与 LLM 提示
- [x] 女王穿云箭战术图（PNG）
- [x] 2D 推演接入面板
- [ ] 连续墙线提取（模板匹配方案）
- [x] 识别全部防御建筑（本仓标注数据 within 0.879 / LOBO 0.820）
- [x] 等级体系 + TH 自动回填 + 撒兵线优化
- [x] Android 标注 App + 对手 OCR/API
- [ ] 屏幕自动检测（瓶颈：需要检测器，不是分类器）
- [ ] 「进攻中」视图 HUD 避让实测

## ⚠️ 已知限制

- 识别：给定裁剪下类型分类 0.879 / 跨阵 0.820；检测环节仍不可用（逐栋命中 0.06–0.16）；高倍档人工标注 ≥42% 错标；
- 墙线：自动提取方案未通过，隔间/墙体两项评分暂 N/A；
- 视觉大模型：可做 OCR（对手名字已接入 RapidOCR），但建筑分类不可靠，不用于识别；
- 平台：仅 Windows + 雷电 1280×720 实测。

## 🔒 隐私与安全

- 不注入、不读游戏内存、不连游戏服务器；
- 仓库不含任何密钥；大模型通道从本机配置或环境变量读取；
- `out/`、`dist/` 为运行时产物，不入库。

## 📄 许可证与第三方

- 本项目：**MIT**（见 [LICENSE](LICENSE)）；
- 评分指标移植自 [clash-blueprint-engine](https://github.com/koniz-dev/clash-blueprint-engine)（MIT）；
- 布局交叉校验参考 [clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator)（MIT）；
- 建筑素材来自社区素材仓库，遵循 Supercell Fan Content Policy；游戏版权归 Supercell，本项目与其无关联。

## ⚖️ 免责声明

仅供学习与研究。请遵守 Supercell 服务条款与当地法律；使用后果自负。

## 🤝 贡献

欢迎 Issue / PR：先跑通 `python -m unittest discover -s tests`，改动请附测试与证据。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 🙏 致谢

- 公开数据与思路：[ClashKing](https://github.com/ClashKingInc/ClashKing)（战争数据 API）、[ClashKingBot](https://github.com/ClashKingInc/ClashKingBot)（数据驱动思路）、[ClashKingAssets](https://github.com/ClashKingInc/ClashKingAssets)（逐级建筑素材）；
- 完整名单见 [ATTRIBUTIONS.md](ATTRIBUTIONS.md)，集成说明见 [docs/CLASHKING.md](docs/CLASHKING.md)。

## 📌 当前状态 / 待办

今天的完成项与明天的待办（含 P0 鼠标点击问题的定位）都在 `docs/STATUS.md`。
