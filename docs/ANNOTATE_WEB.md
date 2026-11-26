# 本地网页标注器（真实战图 → 可分析 JSON）

用于把「部落战侦察截图」标注成项目能读的 layout JSON。

## 用法

`powershell
python tools/annotate_web.py --image out/live/enemy_scout_live.png --port 8765
`

浏览器打开 http://127.0.0.1:8765 ：

1. 依次点**网格四个角**：左上(0,0) → 右上(44,0) → 右下(44,44) → 左下(0,44)
2. 下方选建筑类型，点该建筑**中心**（右键撤销）
3. 填名字（如 @enemy_shadow_th17@）→ 点「导出 JSON」
4. 文件写到 `out/annotate/<名字>_annotated.json`，直接喂给：

`powershell
python tools/enemy_pipeline.py --layout out\annotate\enemy_shadow_th17_annotated.json
`

## 说明

- 只用 Python 标准库，无需安装依赖；不联网、不上传图片（本机 127.0.0.1）。
- 只用点**防御/关键建筑**也能先跑评分；墙可以不用点。
- 误差要求：点击中心 ±1 格内即可（评分/选线按格中心算）。
