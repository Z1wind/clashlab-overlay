# tools/annotate —— TH16 阵型标注工具（本地网页，零依赖）

用浏览器点选修正 `bases/th16/NN/layout.json` 的人工标注：**layout.json 直接预填**，
你只需要把位置不对的方框拖到正确格子、把类型不对的点一下调色板；预填漏掉的补一栋即可。
结果自动保存为 `out/annotate/NN_annotated.json`（与 layout.json 同 schema）+ `out/annotate/summary.json`。

## 启动

    python tools/annotate/start.py

- 默认监听 `http://127.0.0.1:8765/`，并自动打开浏览器；端口被占用会自动 +1 试到 +20。
- 只用 Python 标准库（不需要 numpy / cv2 / npm），页面是单文件 `index.html`（内联 CSS/JS）。
- 常用参数：`--port 9000`、`--host 127.0.0.1`、`--no-open`、`--strict-port`、
  `--root <项目根目录>`（默认按脚本位置推断，即本仓库根）。

## 数据

| 输入 | 说明 |
| --- | --- |
| `bases/th16/01..06/base.png` | 阵型底图（实际是 JPEG 字节，PNG/JPEG 都能读尺寸） |
| `bases/th16/NN/layout.json` | 预填：`{name, grid, note, buildings[{type,tile,source,conf,note}], walls[[x,y]]}` |
| `bases/th16/NN/layouts/*.json` 或 `layout*.json` | 可选「候选方案」：有就出现候选下拉，Q/E 一键切换；没有就只显示预填 |
| `out/annotate/NN_annotated.json` | 输出：同 schema，`note` 末尾追加一行人工校正溯源 |
| `out/annotate/summary.json` | 汇总：每阵建筑数 / 人工修改次数 / 耗时 / 状态（done/skipped） |

坐标约定（与 `clashlab/geo.py`、`clashlab/topdown.py` 一致）：

- 每阵的 `quad` 就写在 `layout.json` 的 `note` 里（`quad=[[上],[右],[下],[左]]`，base.png 原图像素），
  服务端据此求 `tile -> 像素` 单应矩阵 `H` 和逆矩阵 `Hinv` 下发，前端只做矩阵乘法；
- 整数 `tile` = 单元格索引，单元格中心 = `tile + 0.5`，所以**像素 → tile 用 floor**（不是 round）；
- 预填的 `tile` 允许贴边到 `grid`（生产数据 01 阵有 tile=44 的夹边条目），网页点选只会产生 `0..grid-1`。

## 操作

- **点建筑**＝选中；**点空白**＝用当前类型新增一栋；**按住拖动**＝移动位置；**右键**＝删除。
- 选中后点调色板（或按 `1`–`9`）＝改类型；方向键＝微调 1 格。
- 一栋都没问题的阵直接 `Enter`（保存并下一阵）；不想标的 `Space`（保存并标记跳过）。
- 改动后 1.2 秒自动保存；关页面前 `sendBeacon` 兜底保存。

快捷键：

| 键 | 作用 |
| --- | --- |
| `1`–`9` | 选常用类型（选中建筑时＝改它的类型） |
| `Tab` / `Shift+Tab` | 下一栋 / 上一栋 |
| `Backspace` / `Ctrl+Z` | 撤销 |
| `Delete` | 删除选中建筑 |
| `Ctrl+S` | 立即保存 |
| `Enter` | 保存并进入下一阵 |
| `Space` | 保存并标记跳过，进入下一阵 |
| `Q` / `E` | 上一候选 / 下一候选方案 |
| `PageUp` / `PageDown` | 上一阵 / 下一阵 |
| `R` 连按两次 | 重置为 layout.json 预填 |
| `H` / `Esc` | 帮助 / 取消选中 |

## 自测

    D:\Python313\python.exe -m unittest tests.test_annotate -v

`tests/test_annotate.py` 覆盖纯逻辑（不起浏览器）：quad 解析、tile↔像素单应（含透视 quad、
中心/floor/clamp 语义）、schema 校验与规范化、预填续编辑、人工修改差异统计、原子保存/读取
round-trip、summary 聚合、bases 发现与候选方案、生产数据只读校验（quad 在图像内、每栋建筑
单元中心回投命中自身）。

## 实现要点

- `annotate_core.py`：纯标准库逻辑（单应矩阵、schema、原子写 `.tmp → fsync → os.replace`、summary）。
- `start.py`：`ThreadingHTTPServer` 的接口 —— `GET /`（页面）、`GET /api/state`、
  `GET /api/base?th&id&candidate`、`GET /img?th&id`（带 ETag/304）、`POST /api/save`（schema 校验后落盘）。
- `index.html`：单文件前端（canvas 绘制底图/网格/quad/预填框，拖拽/调色板/撤销/自动保存/快捷键）。
- 不修改 `clashlab/**`、不碰 `out/overlay/**`、不依赖任何第三方包。
## 已知限制 / 未做项

- 现有数据里**没有**候选方案（`bases/th16/NN/layouts/*.json` 不存在）；候选切换已实现并用临时 root 验证
  （下拉、Q/E、`candidate` 落盘、候选模式不继承默认方案的人工结果），但真实 6 阵当前只会显示「预填 layout.json」。
- 预填坐标来自历史人工标注（notes 里自述 ±2~3 格误差、包络标定），**不是逐格真值**；工具只降低修正成本，不替代人工判断。
- 网页侧没有自动化 E2E 测试：`tests/test_annotate.py` 只覆盖纯逻辑。页面已用 Edge headless 实测
  （`--dump-dom` / `--screenshot`：标题、32 类调色板、6 阵下拉、41 栋预填、进度文本、无 JS 报错），未接入 CI。
- 墙体 `walls` 只做只读显示（灰色小点），本工具不编辑墙点。
- 一次只能选中一栋建筑（无框选/多选）；撤销是线性 200 步栈，没有分支历史。
- 只绑本机 `127.0.0.1`；端口被占用自动 +1（`--strict-port` 可关）。改 Python 代码需重启进程，
  改 `index.html` 刷新页面即可（`GET /` 是 `no-store` 且每次现读文件）。
- `base.png` 实际是 JPEG 字节（扩展名写 .png），PNG/JPEG 都能读尺寸与显示。
- `out/annotate/` 初始为空；第一次保存时自动创建，不预置任何示例标注。

