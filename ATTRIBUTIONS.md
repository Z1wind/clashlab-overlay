# 致敬与信息来源 / Acknowledgements

> 借用/参考的每个仓库都在这里有链接、作者与落点。Every borrowed/referenced repo is credited with link, author and where it landed.

## 直接借鉴 / Direct borrowings

| 仓库 Repo | 作者 | 借了什么 What | 落点 Where |
|---|---|---|---|
| [koniz-dev/clash-blueprint-engine](https://github.com/koniz-dev/clash-blueprint-engine) (MIT) | [@koniz-dev](https://github.com/koniz-dev) | 7 指标防守评分、S–F、弱点分级、隔间/死区思路 / 7-metric defense score, grades, weak points | `clashlab/layout_score.py`、`defense_findings.py`、`overlay/score_card.py` |
| [Peter537/clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator) (MIT) | [@Peter537](https://github.com/Peter537) | 几何校验口径、尺寸目录、spell-tower 2×2 证据 / validation taxonomy, footprint catalogue | 交叉校验与尺寸表（spell-tower 3→2） |
| [ClashKingInc/ClashKingAssets](https://github.com/ClashKingInc/ClashKingAssets) | [@ClashKingInc](https://github.com/ClashKingInc) | 建筑素材对照 / asset cross-reference | 素材库 |
| [Statscell/clash-assets](https://github.com/Statscell/clash-assets)、[clash-of-clans-data](https://github.com/Statscell/clash-of-clans-data) | [@Statscell](https://github.com/Statscell) | 素材与数据结构 / assets & data schema | 参考资料 |
| [chiefpansancolt/clash-of-clans-data](https://github.com/chiefpansancolt/clash-of-clans-data) | [@chiefpansancolt](https://github.com/chiefpansancolt) | 分级素材来源 / per-level art source | 上游 manifest 来源 |
| Clash of Clans Wiki (Fandom) | 社区 / community | 建筑 hp/dps/range / per-stat values | `clashlab/assets.py` 的 `source_url` |

## 读过未采用 / Read but not used

以下仓库影响了设计判断，但代码未并入 / influenced design, code not merged:

| 仓库 Repo | 作者 |
|---|---|
| [FICTURE7/CoCSharp](https://github.com/FICTURE7/CoCSharp) | [@FICTURE7](https://github.com/FICTURE7) |
| [DFanso/coc-attack-bot](https://github.com/DFanso/coc-attack-bot) | [@DFanso](https://github.com/DFanso) |
| [Royz2123/Clash-of-Clans-AI](https://github.com/Royz2123/Clash-of-Clans-AI) | [@Royz2123](https://github.com/Royz2123) |
| [clashperk/clashofclans.js](https://github.com/clashperk/clashofclans.js) | [@clashperk](https://github.com/clashperk) |
| [enavarrocu/javascript-clash-of-clans](https://github.com/enavarrocu/javascript-clash-of-clans) | [@enavarrocu](https://github.com/enavarrocu) |
| [danielholmes/coc-base-analyser](https://github.com/danielholmes/coc-base-analyser) | [@danielholmes](https://github.com/danielholmes) |
| [Enjoyop/coc-assets](https://github.com/Enjoyop/coc-assets) | [@Enjoyop](https://github.com/Enjoyop) |
| [nep94121-lab/coc-auto-farm-ai](https://github.com/nep94121-lab/coc-auto-farm-ai) | [@nep94121-lab](https://github.com/nep94121-lab) |

## 数据与素材 / Data & assets

- 六阵侦察图与标注：本项目自行采集（`bases/th16/*`，notes 记录置信度）；
- 建筑贴图：社区素材仓库（ClashKing / chiefpansancolt 等），遵循 Supercell Fan Content Policy；
- 布局图片来源：社区阵型站，仅研究使用。

## 版权 / Copyright

Clash of Clans 及相关素材版权归 **Supercell**。本项目与其无关联、未获背书，遵循 [Supercell Fan Content Policy](https://supercell.com/en/fan-content-policy/)。

## 特别致谢 ClashKing / Special thanks to ClashKing

- ClashKingInc/ClashKing — 公开战争/玩家数据 API，本项目的对手 TH/战争成员自动分析直接使用其接口（`clashlab/cocapi.py`）；
- ClashKingInc/ClashKingBot — 设计思路启发：数据驱动优先于纯图像识别（OCR→API 自动化的思路来源）；
- ClashKingInc/ClashKingAssets — 逐级建筑立绘（合成训练集；版权归 Supercell，仅本地训练使用）。

感谢 ClashKing 把这些接口与素材开放给社区。
Thanks to ClashKing for the public data API and assets that make data-driven analysis possible.
