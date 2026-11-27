# ClashLab 使用说明（v0.3.1）

> 非官方工具，与 Supercell 无关；请自行评估 ToS 风险，勿用于官方赛事。

## 1. 启动

- **Windows 覆盖层**：双击 `ClashOverlay.exe`（v0.3.1 起无参数启动会直接打开 PANEL 面板）
- 命令行方式：
  ```
  ClashOverlay.exe --show --mode PANEL --allow-primary
  ClashOverlay.exe --show --mode PANEL --lang zh-hant
  ClashOverlay.exe --show --mode HUD --allow-primary
  ClashOverlay.exe --version
  ```
- **手机标注器**：安装 `ClashLabAnnotator.apk`（Android 7+），首次启动允许存储权限

## 2. 面板（PANEL）

四个标签页：研究 / 阵型 / 采集 / 设置；右上角 `中 繁 EN` 切换语言。

| 快捷键 | 作用 |
|---|---|
| `Insert` | 面板 ↔ HUD 切换 |
| `Delete` | 采集一帧 |
| `F7` | Live 跟随（实时刷新） |
| `F12` | 重载情报 |
| `F6` | 识别对手（截图 → OCR → 名字/TH） |
| `ESC` | 回 HUD / 取消捕获 |

快捷键可在「设置」页改键、清除、恢复默认；面板可置于雷电窗口 右侧/下方/内部。

## 3. 功能前置条件（为什么有些按钮点了没反应）

| 功能 | 需要什么 |
|---|---|
| 评分 / 弱点 / 穿云箭 | **已标注阵型**（JSON）或先「自动采集」出候选 |
| 生成策略（AI） | 已加载阵型 + LLM 配置 |
| 识别对手（F6） | 游戏画面在雷电窗口前台 |
| HUD 显示标注 | 已完成标定（calib） |

状态栏会直接显示：`阵型 未加载/点采集 · 候选 0` —— 这是提示，不是报错。

## 4. 常见问题

1. **双击没反应？** v0.3.1 已修复：无参数启动会打开 PANEL；若仍无窗口，看 `out/overlay/overlay.log`
2. **面板跑到屏幕最右边 / 贴错模拟器？** 多开雷电时优先标题恰为「雷电模拟器」的实例；仍不对就切「设置 → 面板位置」或拖动面板
3. **重复启动没反应？** 单实例保护：第二个实例会写日志并退出（`another ClashLab overlay is already running`）
4. **繁中变成简体？** v0.3.1 修复了打包缺 zhconv 数据的问题；也可 `--lang zh-hant` 强制
5. **数据在哪里？** 与 exe 同目录的 `config/`、`out/`；没有阵型数据时面板会提示

## 5. 一条命令出报告（可选）

```
python tools\report_one.py --layout out\annotate\06_annotated.json
```
输出：`out/enemy_report/<名>_one/` 下的 `report.json` / `arrow_diagram.png` / `summary.md`
