# Changelog

## v0.3.0 (unreleased)

- 合成素材「类型+等级」双头模型（GPU 300 epoch）：type_acc 0.979 / level_mae 1.14（合成集）；
- ClashKing 公开 API 客户端：玩家/部落标签 → 自动 TH 等级与部落战成员 TH，自动回填布局等级；
- 识别重训（473 栋，用户 APK 补标后）：全类 within 0.879 / LOBO 0.820；
- Android 标注 App v0.2：横屏 + 建筑类型/等级文字标签 + 导出 JSON；
- 2D 图分类扩展（经济/兵营/陷阱）+ 面板建筑构成行；放兵线/区域优化；TH1–TH19 数据层与等级体系。

## v0.2.0 (unreleased)
- 等级体系：建筑/兵种/英雄等级参与推演（实测低配兵摧毁率 18.95%→8.55%）；

- TH1–TH19 数据层（reviewed ruleset）与 assets.stats 委托；
- 布阵 → 兵种搭配推荐（弱点判定 + 投放步骤 + YouTube 搜索入口）；
- 放兵线/区域优化（候选枚举 + 自动挑选，base03 17.9%→24.7%）；
- 四角回归模型（社区阵图 + 草地伪标签，import_base 兜底）。

## v0.1.2 (unreleased)

- wargame 引擎与 CLI：确定性兵棋推演 + Monte Carlo 摧毁率；
- qa_e2e 实机 UI 矩阵（本机 7/7 PASS）与报告；
- 识别模型训练/推理/可行性报告（默认 40 epoch：within 0.662 / LOBO 0.503；models/recog_27px.pt、docs/ML_FEASIBILITY.md）；
- 四角标注工具 tools/label_corners/。

## v0.1.1 (unreleased)

- tools/import_base.py：游戏内点开阵型链接 → 截屏 → 自动 44x44 标定 → 生成 base.png + layout_draft.json（含标定合理性检查）。

- 半自动标注工具 `tools/annotate/`：本地网页，layout.json 预填，点选修正，自动保存到 `out/annotate/`。
- 城墙对称补全 `clashlab/wall_symmetry.py`：按建筑分布推断对称并镜像补墙，区分主城墙与独立墙段。
- 识别数据流水线 `clashlab/recog_dataset.py` + `tools/train_from_annotations.py`：标注 → 27px 裁剪 → 训练评估。
- base-link 解析调研 `clashlab/baselink.py`：实测 payload 为 24 字节不透明 token，离线解码不可行（30 项测试 + 探测脚本）。
- README / 教程去 AI 腔重写，补社区维护说明，仓库 description 与 topics 更新。

## v0.1.0 — 2026-11-25

首个开源版本 / first open-source release。

- 覆盖层 HUD / PANEL，进程外零注入；44×44 标定与自动重标定。
- 防守评分（7 指标 → 0–100 + S–F）与弱点归因，接入简报、LLM 提示和面板。
- 女王穿云箭战术图；2D 推演候选落点接进面板（带缓存）。
- 2D 化：`clashlab/topdown.py` 和 CLI，layout 转俯视 PNG + 2D 交换 JSON。
- Windows + Python 3.13 的 GitHub Actions CI；中英双语文档；`--version` 与中文窗口标题。
- MIT 许可；`ATTRIBUTIONS.md` 记录全部借用来源与作者。
