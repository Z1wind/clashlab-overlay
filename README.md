<div align="center">

# ClashLab · 以 LLM 为辅的部落冲突布阵研究器

把一张干净的侦察截图，变成 44×44 格上的防守评分、弱点和战术图。

[![License: MIT](https://img.shields.io/badge/license-MIT-3da639.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-3776ab.svg)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078d4.svg)]()
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![CI](https://github.com/Z1wind/clashlab-overlay/actions/workflows/ci.yml/badge.svg)](https://github.com/Z1wind/clashlab-overlay/actions/workflows/ci.yml)
[![Release](https://img.shields.io/badge/release-v0.1.0-blue.svg)](https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.1.0)

[中文](README.md) · [English](README.en.md) · [教程](docs/教程.md) · [Tutorial](docs/TUTORIAL_en.md)

</div>

ClashLab 是一个以 LLM 为辅的部落冲突（Clash of Clans）布阵研究器（base layout analyzer），主要面向 TH16 阵型。它做的事情可以概括成一条链：截取模拟器里的侦察画面，标定到 44×44 网格，还原成布局 JSON，算出基地布局评分和弱点，再生成战术图或 2D 俯视图。

工具跑在游戏进程之外，以 overlay 的形式贴在雷电模拟器旁边：不注入、不读内存、不连游戏服务器，只处理屏幕上能看到的画面。代码以 MIT 开源（open source），数据和文档也都在这个仓库里。

先说清楚现状。这个版本还有不少没做完的地方和 bug，我会继续补；它现在还不是一个能直接拿去打部落战的成品，更适合当作 Clash of Clans 阵型分析、建筑识别和覆盖层开发的一个试验台。

![PANEL](docs/screenshots/panel.png)

## 最近更新（2026-11-26）

- **兵棋推演** `clashlab/wargame.py`：军队构成 + 投放点 → 确定性 tick 战斗模拟 + Monte Carlo 摧毁率分布（base 03 实测 mean 15.5%，最佳投放点 22.1%），CLI 见 `tools/wargame_cli.py`。
- **实机 UI 验证**：`tools/qa_e2e.py` 一条命令跑 7 项矩阵（HUD/PANEL × 有/无布局、页签切换、缩放重标定、exe 自检），本机实跑 **7/7 PASS**，报告 `docs/QA_E2E.md`。
- **机器学习可行性**：`tools/train_save_model.py` 训练并保存 `models/recog_27px.pt`（within 0.630 / LOBO 0.477；充分训练可到 0.734 / 0.641），推理接口 `clashlab/recog_model.py`，报告 `docs/ML_FEASIBILITY.md`。
- 新增四角标注工具 `tools/label_corners/`（给自动标定模型造数据）。

## 能做什么

- **覆盖层**：HUD 标注（只读、鼠标穿透）和 PANEL 四页（研究 / 阵型 / 采集 / 设置），贴在模拟器客户区旁边。
- **标定**：44×44 DLT 单应，客户区尺寸变化超过 10% 时自动重标定。
- **评分**：7 个指标加权成 0–100 分，给出 S–F 等级和带方位的弱点。
- **战术**：弱点会进简报、LLM 提示和面板；可以出女王穿云箭战术图；支持 2D 推演候选落点。
- **2D 化**：`layout.json` 转成俯视阵型 PNG 和 2D 交换 JSON，方便导进别的 2D 引擎做推演（`python -m clashlab.topdown_cli`）。
- **游戏内导入**：在模拟器里点开阵型链接，运行 python tools/import_base.py --th 16 --id 07 → 自动截屏、44×44 标定，生成 base.png + layout_draft.json，再交给标注工具微调。
- **base link 调研**：分享链接里的 payload 是不可恢复的 24 字节 token，社区没有解码器（详见 [docs/BASELINK_RESEARCH.md](docs/BASELINK_RESEARCH.md)）；在游戏里点开链接再截图是可行替代。

## 安装和运行

需要 Windows 10/11、Python 3.13、雷电模拟器 9（客户区 1280×720），以及 numpy、opencv、pywin32、imgui_bundle、pillow 这些依赖。

```powershell
git clone https://github.com/Z1wind/clashlab-overlay.git
cd clashlab-overlay
python -m pip install -r requirements.txt
python run_overlay.py --show --mode HUD --always-on-top --run-seconds 8
python -m unittest discover -s tests   # 应全部通过
```

第一次跑建议先只开 8 秒看看日志：`out/overlay/overlay.log` 里出现 `target_rect=...`、`rect=(x,y,1280x720)`、`fps summary` 和 `runtime end`，就说明找窗、标定、渲染这条链是通的。模式切换、热键、LLM 配置和排障见[教程](docs/教程.md)。

## 常用命令

```powershell
# 赛前推演：读一个 layout，输出攻防双方的模拟结果
python -m clashlab.prebattle --layout bases\th16\03\layout.json --out out\prebattle

# 女王穿云箭战术图
python -m clashlab.overlay.giant_arrow_diagram --layout bases\th16\03\layout.json --out out\ga.png

# 打成 exe
.\build_overlay.ps1

# 跑测试
python -m unittest discover -s tests
```

## 下载

- [Release v0.1.0](https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.1.0)：`ClashOverlay.exe`（Windows x64，约 90MB）、源码包、`SHA256SUMS.txt`。

不装 Python 的话下 exe 直接跑；想改代码或看数据就从源码装。

## 评分怎么读

| 指标 | 权重 | 状态 |
|---|---|---|
| 大本营保护 | 3 | 可用 |
| 资源仓保护 | 2 | 可用（纯防御标注时为 N/A） |
| 对空防御 | 2 | 可用 |
| 对地防御 | 2 | 可用 |
| 隔间质量 | 2 | N/A，墙数据未补全 |
| 墙体效率 | 1 | N/A，墙数据未补全 |
| 入口控制 | 1 | 可用 |

七项合计 13 分权重，折算到 0–100 后分级：S≥90、A≥80、B≥70、C≥55、D≥40。隔间和墙体两项因为自动墙线提取还没过，现在固定显示 N/A，等数据补齐会恢复。

## 工作方式

```text
雷电 1280×720 --PrintWindow--> 截图 + 44×44 单应
      --> 评分 / 弱点 / 防线环 / 推演 --> ImGui 覆盖层 + PNG
```

截图和标定走 `clashlab/vision.py` 与 `clashlab/geo.py`（坐标换算的唯一入口），评分和弱点归因读 `assets.py` 里的尺寸与属性表，战术部分把弱点整理成简报交给规则引擎或 LLM，最后在覆盖层里画出来，或者导出成 PNG / JSON。

## 已知限制

- **建筑识别还不能用**：27px 同档准确率 0.523；高倍档的人工标注审计后至少有 42% 是错标的，所以那些看起来更高的数字不能信，检测这条路暂时没有可用版本。
- **墙线自动提取没通过**，隔间质量和墙体效率两项指标因此是 N/A。
- **视觉大模型只能做 OCR**：资源数字 4/4，建筑分类只有 3/16。
- **只在 Windows + 雷电 1280×720 上实测过**，别的模拟器和分辨率没有验证。

## 社区维护

仓库目前基本是我一个人在做，所以特别欢迎社区一起把它补完整。下面几类东西都可以直接提：

- **阵型标注**：按 44×44 网格标好的 TH16 阵型（别的本也收）。放到 `bases/<本>/<阵型>/` 下，附一张原始截图和一句标注说明；墙线如果也标了，请单独说明来源。
- **布局 JSON**：`layout.json` 或 2D 交换 JSON。同一个阵型有多份互相校验的最好。
- **识别样本**：干净的侦察帧加上对应 layout，27px 和 70px 两档都缺。识别是目前最大的短板，样本比代码更值钱。
- **算法改进**：评分指标、弱点归因、2D 推演、覆盖层的性能和交互，改哪一块都行。

提交方式有两种：

- **Issue**：bug 用 `Bug report` 模板，贴命令、`out/overlay/overlay.log` 尾部日志和环境信息；功能建议用 `Feature request` 模板，勾选相关模块（overlay / recognition / layout score / tactics / docs-tooling）。
- **PR**：按 `.github/PULL_REQUEST_TEMPLATE.md` 写清改了什么、怎么验证；数据类提交请说明来源（自己截的 / 社区公开的），不要带本机路径和密钥。改代码前先跑一遍 `python -m unittest discover -s tests`。

更细的约定在 [CONTRIBUTING.md](CONTRIBUTING.md) 里。哪怕只是提一个 issue 说说你想要的阵型分析视角，或者把仓库转给需要的人，都是有帮助的。

## 隐私

工具不注入雷电进程、不读游戏内存、不连接游戏服务器；仓库里不含任何密钥（LLM 凭据来自本机配置或环境变量）。除了你自己主动开启的 LLM 调用，画面和阵型数据只在本机流转，不会上传。

## 致谢

借用内容、作者和许可证的完整清单见 **[ATTRIBUTIONS.md](ATTRIBUTIONS.md)**。主要的几处：

- [@koniz-dev](https://github.com/koniz-dev) · [clash-blueprint-engine](https://github.com/koniz-dev/clash-blueprint-engine)：防守评分的 7 个指标和弱点体系
- [@Peter537](https://github.com/Peter537) · [clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator)：几何校验与建筑尺寸目录
- [@ClashKingInc](https://github.com/ClashKingInc/ClashKingAssets)、[@chiefpansancolt](https://github.com/chiefpansancolt)、[@Statscell](https://github.com/Statscell)：素材与数据参考
- [FICTURE7/CoCSharp](https://github.com/FICTURE7/CoCSharp)、[DFanso/coc-attack-bot](https://github.com/DFanso/coc-attack-bot)：读过没采用，但影响了设计判断

## 许可

MIT，见 [LICENSE](LICENSE)。第三方署名汇总在 ATTRIBUTIONS；游戏素材版权归 Supercell，使用遵循 Supercell Fan Content Policy。

仅供学习研究，请遵守 Supercell 的服务条款，使用后果自负。
