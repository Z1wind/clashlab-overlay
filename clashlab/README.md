# clashlab —— 部落冲突赛前布阵研究与战斗副驾（v0.1）

本仓库是《部落冲突战术研究与战斗辅助应用-技术方案》的可运行落地版本。目标是把方案里
"采集 → 识别 → 标定 → 规划 → 校验 → 绘制"这条链路真正在本机跑起来，先在雷电模拟器的
真实《部落冲突》上验证通道与几何，再逐步补齐识别与执行。

**合规红线**：Supercell 的《服务条款》与《公平游戏》政策把自动战斗脚本定义为作弊，
一旦在联网账号上使用自动化（自动撒兵、自动开战），处罚是永久封禁。本仓库默认
`deploy` 为 dry-run，只有显式 `--live` 才会真正下发点击；所有实测请只用小号/私服。
纯离线沙盘、只读副驾（overlay）不属于自动化操作，可以在主号上用于复盘研究。

## 已完成能力

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| ADB 采集 | 可用 | `screencap` 走 `exec-out`，避免 PowerShell 二进制重定向损坏 PNG |
| 地图标定 | 可用 | 石质地基 / 草地 / 红色禁区三种线索求四角菱形，单应变换映射 44×44 网格 |
| 界面状态 | 可用 | base / deploy / dialog（挂机"还在吗"弹窗自动识别并 recover） |
| 建筑识别 | 半自动 | 连通域给候选地块；类型由官方 sprite 模板补；准确率不足时用 `annotate` 人工标注 |
| 撒兵规划 | 可用 | 代价场 + 沿路径 dps 累积的 O(N) 热图，全图 ~20ms，输出 Plan |
| 计划校验 | 可用 | schema / 库存 / 部署区 / 时间预算 / 预测得分 五项 |
| 实时绘制 | 可用 | Tk 透明穿透层 + 独立小窗策略面板，`--hud` 打开 |
| 虚拟桌面 | 可用 | `bench` 在独立 Windows 桌面跑采集与 HUD，物理桌面鼠标/前台不变 |
| 策略研究 | 可用 | `analysis` 出覆盖图/弱侧/防御重心/首打顺序，`study` 出三面板研究图 + JSON |
| 下发 | 有闸门 | `deploy` 默认 dry-run，`--live` 才点；支持按计划多点撒兵 |

## 安装

```powershell
D:\Python313\python.exe -m pip install opencv-python numpy pillow pywin32
```

ADB 与多开器直接复用雷电自带：
- `E:\leidian\LDPlayer9\adb.exe`
- `E:\leidian\LDPlayer9\ldconsole.exe`

## 常用命令

```powershell
# 环境体检：设备、分辨率、前台包、抓帧耗时
python -m clashlab doctor --serial 127.0.0.1:5555

# 抓一帧并分析（输出标注图 + JSON）
python -m clashlab grab --serial 127.0.0.1:5555 --out out\grab

# 离线分析一张图，可选阵型 JSON
python -m clashlab analyze out\live_00.png --layout layouts\th13.json --out out\analyze

# 仿真阵型全链路（不连游戏，用来验证算法）
python -m clashlab demo --out out\demo

# 实时循环（可带 HUD）
python -m clashlab run --serial 127.0.0.1:5555 --seconds 20 --hud --recover

# 虚拟桌面隔离实测：物理桌面鼠标与前台窗口不变
python -m clashlab bench --serial 127.0.0.1:5555 --seconds 15 --recover

# 半自动标注：在截图上点选建筑，生成布局 JSON
python -m clashlab annotate --image out\live_00.png --save layouts\th13.json

# 赛前策略研究：输出三面板研究图 + 结论 JSON（离线，零风险）
python -m clashlab study --layout layouts\th13_sample.json --out out\study

# 下发撒兵点（默认 dry-run）
python -m clashlab deploy --plan out\analyze\plan.json
python -m clashlab deploy --plan out\analyze\plan.json --live
```

## 素材

`assets/coc/` 来自 npm 包 `clash-of-clans-data`（MIT 许可证，图片版权归 Supercell），
按 `buildings/<建筑>/level-N.png` 存放，透明底，可直接做模板与图标。
仅按 Supercell Fan Content Policy 用于本地非商业研究，不再分发。

## 目录

```
clashlab/
  adb.py       ADB 通道（取帧/前台/点击，默认 dry-run）
  geo.py       44x44 等距网格与单应矩阵
  vision.py    标定、界面状态、弹窗、候选地块、模板分类
  assets.py    素材、近似数值表、多尺度模板匹配
  sim.py       代价场 + 热图（O(N) 前向累积）+ 单点推演
  analysis.py  策略研究：扇区入点、路径受击、盲区/重心、首打顺序、三类候选方案
  study.py     研究图渲染（阵型射程 / 覆盖热图 / 撒兵点与路线 + 文字结论）
  planner.py   规则化计划生成与五项校验
  render.py    叠加层与 HUD 小窗的静态合成
  hud.py       Tk 实时绘制层（点击穿透）与策略面板
  vdesk.py     Windows 虚拟桌面隔离与取证
  annotate.py  半自动标注工具
  farm.py      真机侦察采集（状态机 + 锚点 confirmed 元数据，默认不进攻）
  dataset.py   样本聚合（index/usable/studyability/阵型类别）与样本→study 批量研究
  plan_marks.py 策略→屏幕坐标 draw_calls（穿云箭射线/英雄部队落点/拆点/分步）
  prompts.py   人格 + 三档样式 + 卡片与未知项注入 + 落盘缓存
  prebattle.py 赛前情报（info.json + 五段式 brief + 规则化 risks）
  knowledge.py 战术卡检索（BM25 风格加权，空库不编造）
  equipment.py 英雄装备画像与能力映射（模板匹配 <0.7 待人工确认）
  cli.py       命令行入口
```

## 已知边界

1. **建筑分类还没有到生产精度**。夜景（TH13 夜战皮肤）下官方 sprite 与游戏实际渲染存在
   色调差异，纯模板匹配误检率高。下一步按方案第 9 章做数据合成 + YOLOv8 微调：
   用本仓库的 sprite 在真实地基截图上做 domain randomization 合成带标注样本，
   训练 25 类检测器，替换 `vision.detect_structures` 的类型来源。
2. **缩放依赖**。标定依赖画面里能看到完整地基菱形；游戏内缩放最远时最稳。
3. **采集帧率**。雷电 `screencap` 单帧 500–900ms，实时层实际 1–2 fps，
   与方案里"识别 5–8 fps"的预算相比偏低；换 `minicap`/`scrcpy` 的 raw 流可以降到 30ms 级。
4. **下发只在测试号上验证**，主号一律只用副驾（只读）。
5. **研究得分是相对排序，不是真实破坏率**。`score = 打掉血量/总血量 × 时间惩罚 + 到达奖励`，
   只用来在同一座阵里比较入点好坏；不同阵之间不要横向比数值。
6. **风险档位是同批候选内的相对值**（最省的一条算低，1.35 倍以上算高），
   绝对口径需要接入真实兵种血量与防御 dps 表后再标定。
7. **研究目前跑在样例阵 `layouts/th13_sample.json` 上**。真实对手阵型先用
   `annotate` 标成 JSON，再 `study --layout`，链路一致。

---

# 打鱼采集、真实样本与策略标注（v0.2 增补）

v0.2 把三条能力补上：**真机侦察采集**（farm）、**样本聚合与批量研究**（dataset）、
**策略→屏幕坐标标注**（marks），并新增**赛前情报**（prebattle）、**战术知识库**（knowledge）、
**英雄装备画像**（equipment）。下面所有数字都是本机实测，不是估算。

## 1. 打鱼采集 `farm`

```powershell
# 默认 dry-run（只认状态、不真点），先确认识别对不对
python -m clashlab farm --rounds 3

# 真机跑：只侦察采样，绝不点"进攻！"、绝不撒兵
python -m clashlab farm --rounds 6 --live --out out\farm
python -m clashlab farm --rounds 6 --live --mode sample --anchors config\anchors.json
```

产物：`out\farm\farm_report.json`（坐标表 + confirmed 状态 + stats + blockers）、
`out\farm\anchor_log.json`（每个坐标的前后截图判定）、`out\farm\probe\*.png`（85 张证据）、
`out\farm\samples\<id>\{frame.png,meta.json}`（样本，含 quad）、`out\farm\README_farm.md`。

### 实测确认的坐标（1280×720，`config\anchors.json`）

| key | 坐标 | 状态 | 说明 |
| --- | --- | --- | --- |
| battle（夜世界战斗） | 88,645 | confirmed | 打开"开始进攻"面板 |
| attack_close | 1088,133 | confirmed | 面板右上关闭 X（实测比候选 1086,127 偏右下） |
| find（立即寻找） | 951,474 | confirmed | 0 兵状态会被"训练部队后再发起进攻"拦截 |
| edit_army（编辑军队） | 421,570 | confirmed | **只开编成器，不训练** |
| m_battle（主村战斗） | 75,635 | confirmed | 主村入口 |
| m_search（搜索对手） | 197,535 | confirmed | → 弹出"我的军队"开战确认面板 |
| confirm_close | 1237,90 | confirmed | 确认面板关闭 X |
| scout_back / scout_attack | 64,44 / 1150,640 | **false** | 未实测（见下方阻塞） |

### 实测结论与阻塞（必须如实读）

1. **夜世界（建筑大师基地）当前 0/3 兵营**：兵营建筑本身没建，"立即寻找"被
   "训练部队后再发起进攻！"拦截；地图上浮动的"训练"标签悬在空地/营火上，点它打不开训练队列；
   "编辑军队"只打开"选择军队"编成器。→ 需人工先建 1 座兵营，才能再探训练入口。
2. **主村兵力满编 4/4**，`战斗 → 搜索对手` 能走到"我的军队"开战确认面板，但**再往下必须点绿色
   "进攻！"才会匹配到对手**。按本轮红线（不改变奖杯、不进入战斗）**没有点**，因此
   `scout_back` / `scout_attack` 没有任何真机画面可测，锚点里标 false。
3. 6 轮 `--live` 全程未点"进攻！"、未撒兵、未掉杯，结束时模拟器留在主村干净主页（状态机自带
   `back()` 自清，不会残留弹窗）。
4. **人工半自动打通方式**：手动走到侦察视图（战斗 → 搜索对手 → 确认面板点"进攻！"→ 匹配到对手
   基地预览后停手），再跑 `python -m clashlab farm --live --mode sample`，脚本识别到 `scouting`
   即自动落 `frame.png + meta.json + quad`。届时先对侦察视图的返回/进攻按钮做前后截图实测，
   替换 `anchors.json` 里的两个候选值。

## 2. 样本数据集 `dataset`

```powershell
python -m clashlab dataset index --samples out\farm\samples --out dataset\index.json
python -m clashlab dataset ls --index out\dataset_demo\index.json
python -m clashlab dataset study --id s005_bootstrap --out out\dataset_study
python -m clashlab dataset study --all --out out\dataset_study
```

`dataset\index.json` 每样本字段：`id / time / frame{rel,abs} / quad / boundary{confidence} /
buildings{count,source} / labels_source / issues / usable / usable_reason /
studyability(0-100) / studyability_deductions / layout_class / class_evidence / study_figure`。

判定规则（可解释、可追溯）：

- **usable 硬门槛**：meta 可读 + frame 可解码 + quad 四点非退化 + labels 非空；缺 meta、
  labels=null、quad 无效、目录空 → false 并给具体 reason，脚本恒 exit 0。
- **studyability 100 分起扣**：labels 空 −40、quad 无效 −30、建筑 0 个 −35 / <6 −20 / 6-9 −8、
  置信度 <0.25 −10 / <0.15 −20、每条 issue −4，扣分明细落 `studyability_deductions`。
- **阵型类别纯坐标计算**：`corner / ring / square / scatter / hybrid / unknown`，
  依据写进 `class_evidence`（r_mean/r_cv、外中内环占比、四象限占比、corner_ratio、重心偏移）。

当前真实样本数为 0（采集链路卡在"进攻！"闸门），demo 5 个样本里 1 个可用（s005，24 建筑、
square、96 分），其余 4 个 labels=null 按设计判不可用。真实样本到位后把 `--samples` 指过去重跑即可。

## 3. 策略 → 屏幕坐标标注 `marks`

```powershell
python -m clashlab marks --layout layouts\th13_sample.json --profile config\heroes.json `
    --prebattle out\prebattle\info.json --style terse --out out\marks
python -m clashlab marks --layout layouts\th13_sample.json --no-llm --out out\marks   # 纯规则
```

输出 `out\marks\marks.json` 的 `draw_calls` 契约（坐标一律 44×44 格号，像素换算由 UI 用
`Calib.tile_to_px` 做）：

```json
{"version":1,
 "marks":[{"kind":"building","tile":[22,12],"label":"防空","role":"target|snipe|avoid","seq":1}],
 "lines":[{"kind":"giant_arrow","from":[8,16],"to":[30,14],"hits":[[22,12],[12,22]],"label":"…"}],
 "pins":[{"kind":"hero|troop|spell","role":"queen|king|warden|rc|edrag|freeze","tile":[8,16],"count":7,"order":1,"label":"…"}],
 "circles":[{"kind":"freeze|rage|invis","tile":[22,22],"radius":4}],
 "steps":[{"order":1,"text":"…"}],
 "profile":{"used":["giant-arrow"],"missing":[]},
 "cards":["k019"],"source":"rule|llm|merged", "prebattle":{"th":null,"unknown":[…],"brief_chars":884}}
```

实测（th13_sample，新环 1205 格）：穿云箭 `(1,11)→(22,32)` 命中 2 座防空 `(22,32)`、`(12,22)`；
pins 6/6 全在撒兵环内（硬成员校验，越界会 `_snap_to_ring` 退最近合法格并记偏移）；
rule / merged / 模型不可用三种来源都实测；`giant-arrow` 未穿戴时**不出射线**，女王改跟队切入。

## 4. 赛前情报 `prebattle`

```powershell
python -m clashlab prebattle --layout layouts\th13_sample.json --profile config\heroes.json `
    --enemy queen=75,king=75,warden=50,rc=30,cc=40 --out out\prebattle
```

`out\prebattle\info.json` 与 `brief.md`（五段式，实测 728 字 ≤900）。`defense_counts` 逐栋点数核对
（防空 4 / 鹰炮 1 / 散射炮 2 / 地狱塔 2 / X 连弩 2 / 箭塔 4 / 加农炮 4 / 法师塔 2 / 迫击炮 2）。
**TH 等级、敌方英雄等级、CC 兵种、敌方装备、陷阱位置一律允许 `null` 并写进 `unknown`**；
不传 `--enemy` 时四项英雄等级全 null，brief 明写"未获取"，不编数字。

## 5. 战术知识库 `knowledge`

34 张结构化战术卡落 `knowledge\tactics\*.json`，索引 `knowledge\index.json`；
覆盖 4 类 pattern（queen_charge / edrag_rush / hybrid / blimp）、13 组装备组合。
`retrieve(profile, brief, k=3)` 在 th13+edrag+giant-arrow 下召回 3 张并给命中理由（th/army/equipment 加权）。
**诚实性**：B 站只能取到标题+简介（6 张 conf 0.4 标"仅标题级"，4 张 conf 0.5 标"标题+简介级"），
贴吧 robots 禁止自动访问；空库返回 `[]` 并记 `no_knowledge`，绝不编造卡号。

## 6. 英雄装备画像 `equipment`

```powershell
python -m clashlab profile --show
python -m clashlab profile --set queen giant-arrow,invisibility-vial   # 默认不落盘到 config
python -m clashlab equipment detect --image <英雄界面截图>
```

素材：`assets\coc\equipment\` 24 个 128×128 透明底图标、`assets\coc\heroes\` 4 头像、
`assets\coc\spells\` 8 法术，清单 `assets\coc\manifest_equipment.json`（来自 npm
`clash-of-clans-data@0.19.1`，MIT，图片版权归 Supercell）。
`config\heroes.json` 是人工画像（TH13 / 75-75-50-30），`profile_rules` 出 24 条 allowed/effect/note；
**未穿戴的装备 allowed=false 且注明"未穿戴 X，对应策略禁用"**。
`detect_equipment` 多尺度 0.18–0.32 模板匹配，<0.7 一律 `pending`（待人工确认），素材缺失时
返回 `available:false` 不瞎猜。**敌方装备在游戏内不可见 → 固定 `enemy_equipment:"unknown"`**。

## 7. 精度与口径（必须一起读，别只看结论）

| 环节 | 实测 | 口径说明 |
| --- | --- | --- |
| CV 候选定位（5 合成用例 120 目标） | 命中率 **0.408**、平均 tile 误差 **0.75 格**、误检率 **0.183** | 只衡量候选定位，有真值 |
| 真实帧（25 张） | 20 帧能出框；v2 候选 68、模型定型 20；LLM 67 次调用 / 306.75s | 无真值，只报自洽指标，**不宣称类型正确率** |
| 真实帧"0 检出"根因 | 旧 `structure_mask` 的 `s>72` 把洞穴蓝地面整片当前景（命中 71%、mask 非零 0.97） | 已加 `structure_mask_v2`（暖色 H<18\|H>165 且 s>55 或 v>200），仅启发式出框 |
| 撒兵环 | 可撒兵格 base 1084→1205、v_square 1197→1372、v_scatter 444→824 | 占位=建筑+围墙 → 闭运算 k9 → 膨胀1 → 取反 → 去最外圈 |
| 入点边角率（5 case 均值） | **0.200 → 0.000** | 边角带 = 距地图边 ≤2 格 |
| 方案分差 spread_norm | 0.249 → 0.209 | `predicted` 是同批最优=1.0 归一的**相对排序**，非真实破坏率 |
| 模型链 | 默认只留 `deepseek-v4.1-flash`（text 2.5–3s / vision 5.6s） | `glm-5.3-flash` 支持 image_url 但 text 33s、不稳定，仅显式指定才用 |
| 校验器 | 坐标越界只丢该条 adjust（`[soft]`，保留 verdict/strike_order） | 非 JSON / 全空结论才 `[hard]` 拒收 |

**仍然不成立的精度**：合成召回 ~41%（主因在候选检测，oracle 口径也只有 0.392）；
`(8,22)` 这类"贴墙外 1 格"的格子在膨胀 1 格后仍被封锁（最近合法格 `(8,23)`）；
`core_cover_dps / exposed / blind` 是纯阵型量，对军队参数 delta=0（by design）。

## 8. 合规与风险

- `farm` 默认 dry-run，`--live` 才真点；`sample` 模式**不点"进攻！"、不撒兵、不改奖杯**。
- 训练消耗圣水是允许的，但本轮因兵营未建未能验证补兵链路。
- 联网账号上任何自动化都按 Supercell 政策属作弊，可能永久封禁；`--live` 只在测试号上用。
- 所有素材仅本地非商业研究（Supercell Fan Content），不随包分发到公开渠道。
