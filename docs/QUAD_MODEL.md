# 四角回归模型（自动标定兜底）

目标：用模型从阵图预测 44×44 地图的四个角（上/右/下/左），在草地检测失败时作为 import_base 的兜底。

## 数据来源

- 社区阵型图（clashofclans-layouts.com 原图，TH9–TH18，共 38 张，另有 20 张早期下载图）；
- 伪标签：`clashlab.calib.detect_village_quad` 的草地边界检测（在这批图上 **51/57 = 89%** 能给出面积占比 15%–95% 的合理四边形）；
- 局限：伪标签不是人工真值，模型指标反映「对伪标签的拟合误差」，不等于真值精度。

## 流程

```powershell
python tools\collect_quad_images.py      # 下载社区阵型图 -> out/quad_images/
python tools\build_quad_dataset.py       # 草地检测自动标注 -> out/quad_dataset/manifest.json
python tools\train_quad_model.py         # 训练 -> models/quad_model.pt + quad_metrics.json
```

## 模型

- 输入：BGR 图 resize 到 320×180；输出：8 个数（4 角 × x/y，按图宽高归一化）；
- 结构：4 个 conv-bn-relu-maxpool 块（24/48/96/128）+ GAP + FC，sigmoid 输出；
- 训练：smooth-L1，AdamW + cosine，160 epoch，增强（旋转 ±6°、缩放 0.85–1.15、水平翻转同步翻标注）；
- 推理：`clashlab/quad_model.py` 的 `load_model()` / `model.predict(img_bgr)` → `[[x,y]×4]` 像素坐标。

## 接入

`tools/import_base.py`：草地检测失败或面积可疑时，若存在 `models/quad_model.pt` 则用模型预测四角兜底（输出里标 `method=quad-model`）。

## 实测指标

见 `models/quad_metrics.json`（由训练脚本真实产生）。注意：val 只有 11 张，方差很大；下一步应该用 `tools/label_corners/` 的人工标注做真值校准。
