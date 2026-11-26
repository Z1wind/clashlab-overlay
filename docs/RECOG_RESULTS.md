# 标注驱动识别：训练结果对比 / Annotation-trained recognition results

日期：2026-11-26 · 机器：本机 CPU · 协议：stratified 5-fold（同阵内）+ leave-one-base-out（跨阵）· 1 seed · 60 epochs

## 数据

| 数据源 | 阵数 | 样本 | 类别 |
|---|---|---|---|
| 原始 layout.json | 6 | 209 | 18 |
| 用户标注 out/annotate/*_annotated.json | 6 | 154 | 19 |

用户在本轮完成了 6 个阵的人工校正：合计 **188 处人工修改**（移动 22/24/…，删/增若干），总耗时约 38 分钟。

## 结果（同一配置）

| 模型 | within-5fold | LOBO（跨阵） | 多数类基线 |
|---|---|---|---|
| 原始 layout 训练 | 0.435 | （未跑完，已中止） | 0.129 |
| **用户标注训练** | **0.734** | **0.641** | 0.117 |
| 历史基线（3 阵 107 样本，120 epoch） | 0.523 | 0.520 | 0.159 |

## 结论

- 用标注替换原 layout 的坐标后，同阵 5 折从 0.435 → **0.734**，跨阵 LOBO 0.641（历史基线 0.520）；
- 提升主要来自「坐标修正」而非网络变化（网络/增强/epoch 与原始 layout 训练完全一致）；
- 注意：本轮标注时 44×44 网格尚未做 G 校准，坐标仍有 1~3 格漂移；若按「地图最外圈格」口径校准后重标/重训，预计还能提高。

## 复现

```powershell
python tools/train_from_annotations.py --layouts "out/annotate/*_annotated.json" --epochs 60 --seeds 1
# 原始 layout 对照：
python tools/train_from_annotations.py --layouts "bases/th16/*/layout.json" --epochs 60 --seeds 1 --out out/recog/baseline
```

结果 JSON：`out/recog/train_from_annotations.json`（标注）/ `out/recog/baseline/train_from_annotations.json`（对照，未跑完）。
