<div align="center">

# ClashLab · 以 LLM 为辅助的部落冲突布阵研究器

一个**以 LLM 为辅助的部落冲突布阵研究器**：把「阵型采集 → 44×44 网格标定 → 防守评分（0–100 / S–F）→ 弱点归因 → LLM 辅助复核 → 战术图与推演」做成可复现的流水线；进程外覆盖层（零注入、只看画面）只是它的**可视化外壳**。

[![License: MIT](https://img.shields.io/badge/license-MIT-3da639.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-3776ab.svg)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4.svg)]()
[![Tests](https://img.shields.io/badge/tests-86%20passing-brightgreen.svg)]()
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
git clone https://github.com/Z1wind/clashlab-overlay.git
cd clashlab-overlay
python -m pip install -r requirements.txt

# 可见覆盖层（8 秒自退，便于验证）
python run_overlay.py --show --mode HUD --always-on-top --run-seconds 8

# 单元测试（应 86 项全绿）
python -m unittest discover -s tests
```

详细步骤见 [docs/教程.md](docs/教程.md)（环境 / 模拟器 / 模式 / 评分 / 简报 / 打包 / 排障 / FAQ）。

## ⬇️ 下载

- 现成 exe：[Release v0.1.0 · ClashOverlay.exe](https://github.com/Z1wind/clashlab-overlay/releases/download/v0.1.0/ClashOverlay.exe)（Windows x64，约 90MB）
- 完整源码包：[Release v0.1.0 · ClashLab_open_source_v0.1.0.zip](https://github.com/Z1wind/clashlab-overlay/releases/download/v0.1.0/ClashLab_open_source_v0.1.0.zip)
- 校验：[SHA256SUMS.txt](https://github.com/Z1wind/clashlab-overlay/releases/download/v0.1.0/SHA256SUMS.txt)

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

## 🗺 路线图

- [x] 覆盖层 HUD/PANEL + 自动重标定
- [x] 布局评分（0–100 / S–F）与弱点归因
- [x] 布局弱点接入简报与 LLM 提示
- [x] 女王穿云箭战术图（PNG）
- [x] 2D 推演接入面板
- [ ] 连续墙线提取（模板匹配方案）
- [ ] 识别全部防御建筑（当前 27px 同档 0.523，未达标）
- [ ] 「进攻中」视图 HUD 避让实测

## ⚠️ 已知限制

- 识别：27px 同档分类 0.523；检测不可用；高倍档人工标注 ≥42% 错标；
- 墙线：自动提取方案未通过，隔间/墙体两项评分暂 N/A；
- 视觉大模型：可做 OCR（资源数字 4/4 全对），但建筑分类仅 3/16，不用于识别；
- 平台：仅 Windows + 雷电 1280×720 实测。

## 🔒 隐私与安全

- 不注入、不读游戏内存、不连游戏服务器；
- 仓库不含任何密钥；大模型通道从本机配置或环境变量读取；
- `out/`、`dist/` 为运行时产物，不入库。

## 🙏 致敬与信息来源

本项目站在很多公开工作的肩膀上，完整清单（借用内容/作者/落点/许可证）见 **[ATTRIBUTIONS.md](ATTRIBUTIONS.md)**。

特别致敬：

- [@koniz-dev](https://github.com/koniz-dev) · [clash-blueprint-engine](https://github.com/koniz-dev/clash-blueprint-engine)（MIT）—— 防守评分 7 指标与弱点体系来自它的 analyzer；
- [@Peter537](https://github.com/Peter537) · [clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator)（MIT）—— 布局几何校验与尺寸目录，spell-tower 2×2 的独立证据来自其 art manifest；
- [@ClashKingInc](https://github.com/ClashKingInc) · ClashKingAssets —— 建筑素材对照；
- [@chiefpansancolt](https://github.com/chiefpansancolt)、[@Statscell](https://github.com/Statscell) —— 素材与数据结构参考；
- Clash of Clans Wiki（Fandom）—— 建筑数值的来源标注；
- 以及 [FICTURE7/CoCSharp](https://github.com/FICTURE7/CoCSharp)、[DFanso/coc-attack-bot](https://github.com/DFanso/coc-attack-bot)、[Royz2123/Clash-of-Clans-AI](https://github.com/Royz2123/Clash-of-Clans-AI) 等**读过但未采用**的仓库，它们影响了我们的设计判断。

## 📄 许可证与第三方

- 本项目：**MIT**（见 [LICENSE](LICENSE)）；
- 评分指标移植自 [clash-blueprint-engine](https://github.com/koniz-dev/clash-blueprint-engine)（MIT）；
- 布局交叉校验参考 [clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator)（MIT）；
- 建筑素材来自社区素材仓库，遵循 Supercell Fan Content Policy；游戏版权归 Supercell，本项目与其无关联。

## ⚖️ 免责声明

仅供学习与研究。请遵守 Supercell 服务条款与当地法律；使用后果自负。

## 🤝 贡献

欢迎 Issue / PR：先跑通 `python -m unittest discover -s tests`，改动请附测试与证据。见 [CONTRIBUTING.md](CONTRIBUTING.md)。
