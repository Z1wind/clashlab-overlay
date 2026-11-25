# 致敬与信息来源 / Acknowledgements & Sources

> 这个项目站在很多公开工作的肩膀上。下面逐项列出「用了什么、来自谁、怎么用」，以及没采用但启发过我们的仓库。
> Every borrowed idea, dataset and validator is credited here explicitly.

## 一、直接借鉴/移植

### 1. [koniz-dev/clash-blueprint-engine](https://github.com/koniz-dev/clash-blueprint-engine) · MIT · 作者 [@koniz-dev](https://github.com/koniz-dev)
- **借鉴内容**：`@clash/analyzer` 的 7 个防守评分指标定义与权重（大本营保护/仓库保护/对空/对地/隔间质量/墙体效率/入口防守）、0–100 + S–F 等级、弱点分级（critical/weak/info）、隔间 flood-fill 与死区判定思路；
- **落地位置**：`clashlab/layout_score.py`（Python 重写，非逐行照抄）、`clashlab/defense_findings.py`、`clashlab/overlay/score_card.py`；
- **未使用**：其 TS/Node 实现、Next.js 编辑器、game pack 文件（其数据只到 TH15）。

### 2. [Peter537/clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator) · MIT · 作者 [@Peter537](https://github.com/Peter537)
- **借鉴内容**：布局几何校验口径（BOUNDARY/OVERLAP/INVENTORY 分类）、TH1–19 规则集与建筑尺寸目录、art manifest 的精灵包围盒测量法；
- **用途**：六阵交叉校验（`tools/cv_to_validator.py`）、spell-tower 尺寸 3×3→2×2 的独立证据（其 manifest 量得 width_tiles=1.994）；
- **说明**：仅作为外部校验器与数据参照，未把其代码并入运行路径。

### 3. [ClashKingInc/ClashKingAssets](https://github.com/ClashKingInc/ClashKingAssets) · GPL-3.0（素材）
- **用途**：当前版本建筑贴图（`assets.clashk.ing` 规范路径）作为素材对照与补齐参考；**未**直接纳入发行包（避免 GPL 素材与 MIT 代码混同）。

### 4. [Statscell/clash-assets](https://github.com/Statscell/clash-assets) · [Statscell/clash-of-clans-data](https://github.com/Statscell/clash-of-clans-data)
- **用途**：素材/兵种数据格式参考（其 `output/*.json` 无建筑尺寸，故未用于尺寸表）。

### 5. [chiefpansancolt/clash-of-clans-data](https://github.com/chiefpansancolt/clash-of-clans-data) · 社区素材
- **用途**：上游 base-validator 的 art manifest 中记录的素材来源仓库（按等级的建筑图）。

### 6. Clash of Clans Wiki（Fandom）· 社区维护
- **用途**：`clashlab/assets.py` 中建筑 hp/dps/range 的 `source_url` 逐条标注（如 `https://clashofclans.fandom.com/wiki/Firespitter`），代码内可追溯。

## 二、读过但未采用（避免重复造轮子，也向作者致敬）

| 仓库 | 作者 | 我们得到什么 |
|---|---|---|
| [FICTURE7/CoCSharp](https://github.com/FICTURE7/CoCSharp) | @FICTURE7 | 游戏 CSV 字段语义（buildings.csv 的 Name/TID/Width/Height）参考；协议客户端未采用（过时且违规风险） |
| [DFanso/coc-attack-bot](https://github.com/DFanso/coc-attack-bot) | @DFanso | 「用视觉大模型直接读基地」这条思路的启发（我们实测了 VLM 路线） |
| [Royz2123/Clash-of-Clans-AI](https://github.com/Royz2123/Clash-of-Clans-AI) | @Royz2123 | 简化战斗模拟器的设计参考（未采用） |
| [clashperk/clashofclans.js](https://github.com/clashperk/clashofclans.js) | @clashperk | 官方 API 封装研读；官方 API 不暴露布局，未采用 |
| [enavarrocu/javascript-clash-of-clans](https://github.com/enavarrocu/javascript-clash-of-clans) | @enavarrocu | 早期布局规划器，仅浏览 |
| [danielholmes/coc-base-analyser](https://github.com/danielholmes/coc-base-analyser) | @danielholmes | 「按战争基地规则批量分析」的概念参考 |
| [Enjoyop/coc-assets](https://github.com/Enjoyop/coc-assets) | @Enjoyop | 素材/CSV 仓库调研 |
| [nep94121-lab/coc-auto-farm-ai](https://github.com/nep94121-lab/coc-auto-farm-ai) | @nep94121-lab | sendevent 帧序列与资源数字 OCR 思路参考 |

## 三、数据与素材

- 六阵侦察图与布局标注：本项目自行采集/标注（`bases/th16/*`，notes.md 内逐条记录置信度与来源）；
- 建筑贴图：`assets/coc/` 来自社区素材仓库（含 ClashKing、chiefpansancolt 等），遵循 Supercell Fan Content Policy；
- 布局图片来源（部分阵型 base.png）：clashofclans-layouts.com 等社区阵型站，仅作研究使用。

## 四、工具与生态

- [DeepSeek Harness](https://github.com/deepseek-ai)（本项目的开发/评审环境）；
- imgui_bundle / PyInstaller / OpenCV / NumPy / pywin32 等开源库；
- 大模型通道由使用者本地配置（astrbot provider 或环境变量），不随仓库分发任何密钥。

## 五、版权声明

Clash of Clans 及相关素材版权归 **Supercell** 所有。本项目与 Supercell 无关联、未获其背书，遵循 [Supercell Fan Content Policy](https://supercell.com/en/fan-content-policy/)。若任何权利方认为本项目内容不当，请联系移除。
