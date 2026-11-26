# 布阵 → 兵种搭配推荐（STRATEGY）

一句话：读 layout.json，用 clashlab.defense_findings / clashlab.layout_score 的弱点判定主攻方向，
从 knowledge/strategies.json 选模板，输出「兵种 + 数量、为什么、3–5 步投放顺序、YouTube 搜索入口」。
不联网抓取、不下载、不伪造具体视频 ID。

## 用法

### CLI（人类可读）

    D:\Python313\python.exe tools/strategy_cli.py --layout bases/th16/03/layout.json --th 16

输出：布局名 / TH / 判定（reason）/ 信号（对空、对地、大本营中心度、有效隔间、防御数、墙数）/
每条推荐的 archetype、置信度、why、兵种、法术、投放顺序、搜索链接 / 英雄装备参考。

### CLI（JSON，给面板/脚本）

    D:\Python313\python.exe tools/strategy_cli.py --layout bases/th16/03/layout.json --th 16 --json

JSON 顶层字段：

| 字段 | 含义 |
|---|---|
| layout | {name, grid, buildings, walls} 摘要 |
| th | 本次使用的大本营等级 |
| reason | air-gap / th-bias / compartment-density / general |
| reason_label | 中文判定标签 |
| signals | [{name, value}]，含 air-coverage / ground-coverage / th-centrality / compartments / useful-compartments / defenses / walls |
| recommendations | 推荐列表（见下） |
| hero_equipment | {th, reference_only, disclaimer, heroes} |

可选参数：--limit N（默认 3）、--th（默认 16，范围 1–19）。

### Python API

    from clashlab import strategy

    recs = strategy.recommend("bases/th16/03/layout.json", th=16)
    recs = strategy.recommend(layout_dict, th=16, limit=3)

    reason, signals = strategy.detect_signals(layout_dict)   # CLI / 面板用
    info = strategy.analyze_layout(layout_dict)              # 同上，可读字典
    eq = strategy.hero_loadout(16)                           # 英雄装备参考
    guides = strategy.hero_guides(16)                        # 兼容旧调用

### 推荐条目 schema

| 字段 | 类型 | 说明 |
|---|---|---|
| id | str | 模板 id，如 air-edrag |
| name | str | 中文模板名 |
| archetype | str | air / ground / hero-dive / hybrid |
| th | int | 本次 TH |
| troops | dict[str,int] | 兵种 → 数量（法术已拆出） |
| spells | dict[str,int] | 法术 → 数量 |
| why | str | 引用该布局的具体弱点（对空缺口 / 大本营偏心 / 隔间密度） |
| reason | str | 主判定；无法判定时固定 general |
| steps | list[str] | 3–5 条投放顺序 |
| videos | list[{title,url}] | 1–3 条 YouTube 搜索页链接 |
| source | str | 模板来源标签 |
| confidence | float | 0–1，模板置信度（不是胜率） |
| matched_signals | list[str] | 本条命中的弱点标签 |

## 判定规则（由布局特征驱动）

阈值来自 layout_score 的 7 指标与 defense_findings 的三项干净指标：

| 条件 | reason | 首选 archetype |
|---|---|---|
| 对空覆盖 < 90%，或 air-coverage finding 为 weak/critical | air-gap | air |
| 大本营中心度 < 0.85，或 town-hall-protection finding 为 weak/critical | th-bias | hero-dive |
| 有效隔间 ≥ 5（或闭合隔间 ≥ 6，或 finding 文本提到「隔间」） | compartment-density | ground |
| 空布局 / 没有防御建筑 / 以上都不命中 | general | hybrid |

优先级：air-gap > th-bias > compartment-density > general。
同一布局同时有对空缺口和大本营偏心时先给空军；想强制看英雄切入，可单独看 detect_signals 的
th-centrality 或调整阈值（阈值集中在本文件，便于复核）。

TH 数据覆盖 TH13–TH19；TH 不在该范围或数据缺该档时返回 general 兜底，
不会拿别的 TH 的数量硬套。

## 数据文件

### knowledge/strategies.json

12 条模板，覆盖 TH13–TH19 的 air / ground / hero-dive / hybrid 常见 meta：

- id / name / archetype
- weakness_tags：air-gap / th-bias / compartment-density / general
- troops_by_th：{"13": {"electro-dragon": 7, "balloon": 12, ...}, ..., "19": {...}}
  （数据里法术与兵种混排，模块输出时按 SPELL_IDS 拆成 troops / spells）
- why：模板层面的打法理由（布局层面的 why 由模块结合 findings 生成）
- steps：3–5 条投放顺序
- video_queries：1–3 条固定搜索查询（模块会把其中的 TH 统一成请求的 TH）
- source / confidence：来源标签与置信度

### knowledge/hero_equipment.json

按 TH13–TH19 给已解锁英雄（queen / king / warden / royal-champion）的装备组合与一句话提示；
不同 TH 解锁的英雄不同，缺项表示该档骨架未补，不代表不存在。
这是参考骨架，disclaimer 明确写「参考建议，非官方数据」；新装备/新英雄未核验的留空待补。

## 视频链接与免责声明

- 所有视频链接都是 YouTube 搜索结果页：
  https://www.youtube.com/results?search_query=<urlencoded query>
- 查询由「兵种中文名 + TH」自动生成，并附 1–2 条策划好的固定查询；固定查询里写死的
  TH16 等会被替换成本次请求的 TH，不会拼出「TH16 ... TH13」。
- 不抓取、不下载、不缓存、不转存任何第三方视频/字幕/封面；不生成也不猜测具体视频 ID
  （不会出现 watch?v=...、youtu.be/...、/embed/...）。
- 搜索结果是 YouTube 的实时结果，可能受地区、登录状态、视频下架影响；本工具不保证其准确性、
  可用性或内容质量，也不代表对这些内容的认可。观看请遵守 YouTube 服务条款。
- 本项目只提供「搜索入口」，不是攻略内容的托管方或分发方。

## 数据来源与诚实边界

- 模板是社区 meta 汇总 + 本项目 TH16 六阵特征表的经验整理，不是官方数据，也没有用真实战报逐场校准；
  confidence 只是模板可信度标签，不是胜率。
- TH13–TH16 的常见组合参考较多；TH17–TH19 的数值与 meta 变化快，置信度应视为更低，导入前请人工核对。
- 兵种/法术数量是起点模板：实际要按兵营容量、英雄装备、对手援军和临场侦察调整。
- 布局特征完全取决于 layout.json 的质量：识别错一栋防空/大本营，推荐方向就可能反。
  识别未覆盖的 TH 档位请先看 docs/TH_SUPPORT.md（若存在）与识别模块的限制。
- 本模块不做路径规划/战斗模拟；需要量化推演请用 clashlab/wargame.py（另一套确定性 tick 模型）。
- 面板/PANEL 的接线由 Lead 负责；本模块不改 prebattle/panel，只提供 recommend / detect_signals /
  hero_loadout 三个入口。

## 测试与复现

    D:\Python313\python.exe -m unittest tests.test_strategy -v

12 项契约测试：

1. 空布局 / None 仍返回 general；
2. 无明显弱点（满覆盖 + 中心大本营）返回 general；
3. 对空 0% → 首条 air、reason=air-gap、why 含「对空」；
4. 大本营贴角 → 首条 hero-dive、reason=th-bias、why 含「大本营」；
5. 6 个闭合隔间 → 首条 ground、reason=compartment-density、why 含「隔间」；
6. th=13/16 的数量模板不同、视频 URL 含对应 TH；
7. 所有视频都是搜索页 URL，无 watch?v= / youtu.be/ / /embed/ / /shorts/；
8. 推荐字段完整（archetype/troops/why/steps/videos/reason/th/source/confidence）；
9. 同输入两次输出逐字节一致（确定性）；
10. strategies.json ≥12 条、每条有 source/confidence/3–5 步/1–3 查询、覆盖 TH13–19；
    hero_equipment.json 有 13–19 档且 disclaimer 含「参考」；
11. CLI --json 与人类可读输出均 exit 0、JSON 可解析、含搜索链接与「推荐」；
12. recommend / detect_signals 同时接受 layout dict 与 layout.json 路径。

全量回归：

    D:\Python313\python.exe -m unittest discover -s tests

## 文件

- clashlab/strategy.py — 弱点判定、模板选择、why/steps/videos 生成、装备读取
- knowledge/strategies.json — 12 条兵种组合模板（TH13–19）
- knowledge/hero_equipment.json — 英雄装备参考骨架（TH13–19）
- tools/strategy_cli.py — CLI（表格 / JSON）
- tests/test_strategy.py — 12 项契约测试
- docs/STRATEGY.md — 本文档

## 后续（未开始）

- Lead 把 recommend / detect_signals / hero_loadout 接进 prebattle 输出与 PANEL 行；
- 战术卡（knowledge/tactics/）与英雄装备 UI 的联动；
- 用真实战报/回放校准模板数量与置信度；
- TH17–TH19 新兵种/新装备的人工核对与补档。
