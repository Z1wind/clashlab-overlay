# 竞品与可借鉴项目调研（GitHub，2026-11-27）

> 搜索关键词：clash of clans overlay / analyzer / computer vision / layout / bot；数据来自 GitHub Search API（按 stars 排序）。

## 直接相关

| 项目 | Stars | 语言/许可 | 做什么 | 可借鉴 |
|---|---|---|---|---|
| keanuddn/coc-base-analyzer | 2 | Python | 截图 → CV 识别建筑 + 判阵型 + 陷阱概率 + 按 TH 出进攻方案；monorepo（data-pipeline/ml/knowledge-base/backend/frontend）| **架构**：知识库与模型分离，游戏事实全部来自人工整理的知识库，不靠 LLM 记忆（与我们方向一致）；也把「数据管线」独立成层 |
| danielholmes/coc-base-analyser | 20 | Scala | 按**战争阵规则集**批量分析部落成员阵型，出表格 + 单阵深入分析；有 VillageJsonParser | **规则化评分**：把评分拆成可读规则（我们 P1 要做的）；布局 JSON 解析模式 |
| JawadAhmadKhan04/COC | 4 | Python | COC 阵型布局识别系统（CV） | 同类 CV 路线，可对照失败模式 |
| koniz-dev/clash-blueprint-engine | 3 | TS / MIT | 生产级**布局设计/校验/分析/模拟引擎**，游戏无关、数据包驱动；像 CAD 不像画图 | **布局数据层**：44×44 逐格 + 校验规则 + 数据包设计，可参考/复用其设计（我们目前墙是折线，缺逐格校验）|
| Leixien/pixelchief | 1 | Python | BasePilot 分支：截图 + CV + 点击的自动挂机，单 exe 内置 OCR，明确「无内存读取/无封包/无改客户端」 | **工程化**：单 exe 打包、OCR 内置、只读哲学的对外表述 |
| staticmooniq/RaidR | 1 | Python / MIT | CV+OCR GUI 自动化**研究测试床**（Windows 黑盒 UI 遥测） | **测试方法**：把 CV 管线当黑盒研究，记录可复现实验 |
| jaredfiacco2/ClashOfClans_API | 13 | Python | 用 GCP 静态 IP 调 Supercell 官方 API | 解释了社区拿 API 的门槛（固定 IP）——我们不再走这条路 |
| norecha/pokubot · ChackBR/MyBot_v7 | 178 / 95 | Java | 自动打资源 bot | **不借鉴**：违反 ToS，方向不同 |

## 结论（对我们的意义）
1. **没有成熟竞品做「覆盖层 + 截图分析」**：搜索第一名就是我们自己的仓库；直接竞品 keanuddn 还在早期，说明这个生态空白真实存在。
2. 值得学的三件事：**规则化评分**（danielholmes）、**布局数据层/校验**（clash-blueprint-engine）、**知识库与模型分离**（keanuddn）。
3. 所有成功项目都强调「只读/不碰内存/不碰封包」，与我们一致；bot 类项目 star 高但 ToS 风险大，不跟进。
4. 我们的差异化：War 场景 + 穿云箭/战术图 + 三语 + 手机标注器；短板是自动识别与数据量。
