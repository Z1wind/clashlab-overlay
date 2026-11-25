# 进度记录与明天继续（2026-11-25 23:35 收工）

## 今天做完的
- 覆盖层/评分/战术图/2D 化上线；GitHub 仓库 + Release v0.1.0；README 去 AI 腔 + 关键词 + 社区维护段；
- 半自动标注工具 `tools/annotate`（预填、点选、自动保存、快捷键）；
- **网格校准（G）**：4 角可拖 + 方向键微调 + `/api/quad` override（优先于 layout.json，可重置）；
- 网格标定口径（用户裁定，红线）：**44×44 = 整张地图，四角取地图最外圈格边界，不是最外侧建筑/墙**；已写进 UI 提示、README、中英教程、COLLAB.md；
- `tools/import_base.py`：游戏内点链接 → 截屏 → 自动标定 → base.png + layout_draft.json；
- base link 解码调研结论：不可行（24B 不透明 payload）；
- 城墙对称推理 `clashlab/wall_symmetry.py`；标注→训练流水线 `clashlab/recog_dataset.py` + `tools/train_from_annotations.py`；
- 修复：截图没截全时角点落在图外被拒 → 现在允许超出 1 张图尺寸（实测 POST 带 `(1338.1,-180.9)` 角点返回 200）。

## 当前数据状态
- `bases/th16/02` 有用户少量标注（`out/annotate/02_annotated.json` 11,778 B）；
- `out/annotate/01_annotated.json` 被误删，需重标；
- 标注服务：`python tools/annotate/start.py`（当前在 8765 后台跑着；关掉窗口即停）。

## 明天继续（按优先级）
1. 刷新页面（Ctrl+F5）→ G 校准网格（四角贴地图最外圈格）→ 标 2 个阵/TH，重点是阵 01、02；
2. 标完跑 `python tools/train_from_annotations.py --layouts "bases/th16/*/layout.json" "out/annotate/*.json"`，看准确率相对基线 0.523 的变化；
3. 若标注顺利，再做自动标定增强（用墙格/建筑格做自校准，减少手拖）；
4. 收尾：撤销 GitHub token（权限过大）、更新 README 截图（校准后界面）。
