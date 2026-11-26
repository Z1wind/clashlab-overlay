# 等级体系（兵种/英雄/建筑等级 → 摧毁率）

现实里对手不是满级、我们也不是满级，所以推演必须吃三个等级输入：

| 输入 | 怎么传 | 说明 |
|---|---|---|
| 敌方建筑等级 | `layout.json` 里每栋建筑加 `"level": N`（或用 `tools/set_levels.py` 批量写） | 按该 TH 的 reviewed 最高等级归一化，1 级≈0.35、满级=1.0 |
| 我方兵种等级 | `simulate_once(..., troop_levels={"giant": 7})` / CLI `--troop-levels giant=7` | 未传 = 满级；每级 hp×1.07、dps×1.08 |
| 我方英雄等级 | `hero_levels={"queen": 80, "king": 75}` / `--hero-levels` | 折算成军队整体 dps 加成（0.5–1.0） |

## 用法

```powershell
# 1) 给阵型写等级（原文件会备份 .bak）
python tools\set_levels.py --layout bases\th16\03\layout.json --levels "cannon=16,x-bow=5,archer-tower=10"

# 2) 推演时带上自己的兵种/英雄等级
python tools\wargame_cli.py --layout bases\th16\03\layout.json \
  --army '@out\wargame\army.json' --trials 20 --seed 1 \
  --troop-levels giant=3,wizard=3 --hero-levels queen=10,king=10
```

## 实测（base 03，`{giant:10, wizard:12}`，20 trials，seed=1）

| 场景 | 摧毁率 mean | p10 | p90 | best 投放点 |
|---|---|---|---|---|
| 满级建筑 + 满级兵种 | **18.95%** | 10.53% | 29.21% | (1,42) 28.07% |
| 低等级建筑（cannon16/x-bow5/archer10/air-def8/inferno3） | **21.05%** | 13.16% | 31.84% | (1,42) 30.70% |
| 满级建筑 + 低等级兵/英雄（giant3/wizard3/queen10/king10） | **8.55%** | 2.63% | 18.42% | (42,42) 18.42% |

结论：
- 敌方建筑降级 → 摧毁率 +2.1 个点（同一套军队更好打）；
- 我方兵种/英雄降级 → 摧毁率直接砍半（18.95% → 8.55%），所以「按自己的真实等级算」非常关键。

## 实现

- `clashlab/levels.py`：统一缩放曲线（纯函数、越界 clamp、满级=1.0）；
- `clashlab/th_data.py`：`stats(name, th, level=None)` 支持等级缩放，并标 `level_estimated`；
- `clashlab/wargame.py`：`parse_layout` 读建筑 `level`；`simulate_once/run` 新增 `troop_levels` / `hero_levels`；
- `clashlab/deploy.py`：候选线评估同样透传等级，所以「按你的等级推荐最优撒兵线」。

## 局限（诚实）

- 等级曲线是近似（官方没有逐级公开表），数值只保证相对排序；
- 英雄等级折算成军队 dps 加成是粗粒度近似（没有单独建模英雄技能）；
- 识别层还没识别等级：需要你在标注工具里标 2–3 阵等级，再训练等级头（`docs/LEVELS.md` 下一节会补指标）。

## A 方案：TH16 满级回填（2026-11-26 落地）

6 个已标注阵（151 栋）按 reviewed ruleset 的 TH16 最高等级回填 `buildings[].level`：

`
python tools\apply_max_levels.py --th 16            # 补缺失（默认）
python tools\apply_max_levels.py --th 16 --overwrite  # 全量覆盖
`

关键等级（`knowledge/th_ruleset.json` 的 max_levels）：cannon 21 / x-bow 11 / air-defense 14 /
inferno-tower 10 / scattershot 5 / monolith 3 / eagle-artillery 7 / town-hall 16 / clan-castle 12。

回填后实测（`out/annotate/03_annotated.json`，`{giant:10, wizard:12}`，20 trials，seed=1）：

| 场景 | 摧毁率 mean | p10 | p90 |
|---|---|---|---|
| 满级阵 | **22.32%** | 13.93% | 32.86% |
| 同一阵所有建筑降到 40% 等级 | **39.82%** | 21.07% | 57.50% |
| 满级阵 + 低配兵/英雄（giant3/wizard3/queen10/king10） | **7.32%** | 0.00% | 14.29% |

备份在 `out/annotate/NN_annotated.json.bak_lv`；人工修正在标注工具的「等级 Lv」输入框里改即可。

**局限**：这 6 个阵来自布局站，按满级假设回填；若实际对阵玩家有未满级建筑，请在标注工具里改对应那几栋，
推演会自动用新等级。配色自动识别（`tools/infer_levels.py`）目前不可靠，需等人工等级标签做校准。
