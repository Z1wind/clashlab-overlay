# Changelog

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
