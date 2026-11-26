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

## 2026-11-26 重训（用户补标后，6 阵 262 栋）

数据：`out/annotate/01..06_annotated.json`（262 栋，32 类；仅防御类 190 栋 / 19 类）。
命令：

`powershell
python tools\train_save_model.py --layouts "out\annotate\*_annotated.json" --epochs 40 \
  --models-dir models\all6_all --checkpoint recog_all6.pt
python tools\train_save_model.py --layouts "out\annotate\*_annotated.json" --only-defense --epochs 40 \
  --models-dir models\all6_defense --checkpoint recog_all6_def.pt
`

| 配置 | 样本 | 类别 | within-5fold | LOBO | 产物 |
|---|---|---|---|---|---|
| 6 阵 · 全部类型 | 262 | 32 | **0.718** | **0.581** | models/all6_all/recog_all6.pt |
| **6 阵 · 仅防御类** | 190 | 19 | **0.853** | **0.767** | models/all6_defense/recog_all6_def.pt |

分阵 LOBO（仅防御模型）：01 0.830 / 02 0.625 / 03 0.929 / 04 0.958 / 05 0.917 / **06 0.278**。
06 只有 18 栋，跨阵最不稳定；02 的 0.625 主要是经济类混标错误被去掉后仍缺样本。

对照（同日之前）：旧 154 样本全类模型 within 0.662 / LOBO 0.503；两阵 168 样本全类 within 0.571 / LOBO 0.355。
结论：**补标 + 只保留防御类**是这轮提升的主因；识别链路现在有可用的跨阵泛化（LOBO 0.767）。

局限：颜色/等级仍未进标签；06 阵样本太少；经济类不参与训练（只做布局用）。

## 2026-11-26 15:45 合并 APK 导出后再训（473 栋，含用户补标的零碎建筑）

用户用 Android APK 补标 03–06 阵（导出 JSON 合并后 6 阵共 **473 栋**，等级全部回填）：

| 配置 | 样本 | 类别 | within-5fold | LOBO | 产物 |
|---|---|---|---|---|---|
| 全类（32 类） | 473 | 32 | **0.8795** | **0.8199** | models/v2_all/recog_v2_all.pt |
| 仅防御（19 类） | 283 | 19 | **0.8799** | **0.8092** | models/v2_defense/recog_v2_def.pt |

分阵 LOBO（全类）：01 0.814 / 02 0.630 / 03 0.987 / 04 0.883 / 05 0.895 / **06 0.724**（比补标前的 0.278 大涨）。
对照：262 栋全类 within 0.718 / LOBO 0.581；154 栋旧模型 0.662 / 0.503。

结论：**06 阵补标是这轮最大收益**；全类模型现在 LOBO 0.820，已明显优于仅防御（0.809），
推荐作为默认识别模型；仅防御模型保留作对照。
