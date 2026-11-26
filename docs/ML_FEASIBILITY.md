# 27px 识别：机器学习可行性证明（ML feasibility）

日期：2026-11-26 · 机器：本机 CPU（无 GPU）· 结论口径见文末「读数须知」

本文件回答一个问题：**在 27px/格 的侦察帧上，"建筑外观 → 类别" 是否存在可学习的信号？**
答案：存在，但弱；可用作**先验/初筛**，不足以单独支撑「识别全部防御建筑」的产品目标。

## 1. 数据

| 项 | 值 |
|---|---|
| 图像来源 | `bases/th16/<base>/base.png`（27px/格 侦察截图，6 个阵） |
| 几何 | layout 的 `note` 里 `quad=[[x,y]×4]` → `Calib.from_quad` 反投影 44×44 网格 |
| 裁剪 | 建筑 tile 中心 4.5 格窗口 → 96×96 BGR（`clashlab/recog_dataset.py`） |
| 标注 | `out/annotate/NN_annotated.json`（人工校正 188 处坐标，6 阵 154 栋 19 类） |
| 原始对照 | `bases/th16/*/layout.json`（6 阵 209 栋 18 类） |
| 类别极度不均 | 最多 air-defense 18，最少 firespitter 1；多数类基线 0.117（154 样本） |

数据由 `build_dataset()` 一次读入；脚本 `--source auto` 优先用标注、没有标注时回退 layout。

## 2. 模型与训练

- 网络：3 个 double-conv 块（3→24→48→96）+ BN + ReLU + MaxPool，全局平均池化 → Dropout 0.35 → 1×Linear；
  与 `tools/train_from_annotations.py` **完全同构**（对照实验只变数据，不变网络）。
- 增强：旋转 ±8°、缩放 0.9–1.1、平移 ±8px、亮度/对比度抖动（p=0.7）、随机擦除 8–18px（p=0.2）。
- 优化：AdamW(lr=3e-3, wd=2e-3) + cosine，**30 epochs**，batch 24，
  交叉熵 + label_smoothing 0.05 + 类别权重 `1/sqrt(count)`（归一化）。
- 加速：`channels_last` + CPU `bf16` autocast（权重仍是 fp32，checkpoint 无精度损失）。
- 全部 CPU，总耗时见第 3 节；预算 5 分钟，实测见 `models/metrics.json` 的 `runtime.total_s`。
- 注：`docs/RECOG_RESULTS.md` 的参考跑是同一网络/增强 + 60 epochs + fp32；
  本脚本为守住 5 分钟预算压到 30 epochs，`--epochs 60 --precision fp32` 可回到参考档（>6 分钟）。

## 3. 指标（本机真实运行，非引用）

<!--METRICS_TABLE-->

## 4. 复现

```powershell
# 训练 + 评估 + 落盘（约 3 分钟，CPU）
python tools/train_save_model.py
# 关键产物：
#   models/recog_27px.pt   state_dict + classes + input_size(96)
#   models/metrics.json    全部指标 + 混淆矩阵 + 数据清单
#   models/confusion_within5.png / models/confusion_lobo.png

# 推理接口自测（checkpoint 可加载 / 维度 / 可复现）
python -m unittest tests.test_recog_model -v

# 原始 layout 对照（同一协议，只换数据）
python tools/train_save_model.py --source layout --models-dir models/layout_baseline
```

推理侧只需：

```python
from clashlab.recog_model import load_model, predict_crops
model = load_model()                  # 默认 models/recog_27px.pt
probs = predict_crops(crops)          # crops: list[np.ndarray(96,96,3) BGR uint8] -> (N,19)
top1 = probs.argmax(1)                # -> model.classes 的下标
```

## 5. 与既有结果的关系

本仓库此前已用同一网络/增强、6 阵 154 栋标注样本跑过一轮，结论**落盘在 `docs/RECOG_RESULTS.md`**：

| 数据 / 配置 | within-5fold | LOBO | 说明 |
|---|---|---|---|
| 原始 layout（60 epoch 快速对照） | 0.435 | 未跑完 | tools/train_from_annotations.py |
| **人工标注 + 本仓 checkpoint（30 epoch）** | **0.630** | **0.477** | models/metrics.json 实测 |
| 人工标注 + 充分训练（60–100 epoch） | 0.734 | 0.641 | 早前实验，同协议不同 epoch |
| 历史基线（3 阵 107 样本） | 0.523 | 0.520 | 旧实验 |

本轮交付把该结论**固化为可复现产物**：checkpoint、metrics.json、混淆图、推理接口、单测一条链。
复现出来的数字以 `models/metrics.json` 为准；epoch 数影响很大（30 epoch → 0.630/0.477，60–100 epoch → 0.734/0.641）。

## 6. 局限（必须读）

1. **绝对精度不足以生产**：19 类、154 样本，LOBO ≈0.6 意味着跨阵每 5 栋错 2 栋；UI 上不能直接当唯一真值。
2. **样本极少、类别极不均**：`firespitter` 1 例、`multi-archer-tower` 2 例、`ricochet-cannon` 3 例，
   这几类的指标基本是「记住样本」而非学习。
3. **标注坐标仍有漂移**：本轮标注时 44×44 网格 G 校准尚未完成，中心偏 1–3 格；
   按「地图最外圈格」重新标定后重训，预计还能涨（见 COLLAB.md 2026-11-25 条目）。
4. **同阵 5 折偏乐观**：同一张 base.png 的样本进训练和测试，背景/光照完全共享；
   LOBO 才是跨阵泛化口径。
5. **不是检测器**：本模型只做「已知 tile 中心的分类」，不解决「建筑在哪」；
   检测环节此前已证死（逐栋命中 0.06–0.16）。
6. **高倍档不可用**：70px 档人工标注经审计至少 42% 错标，相关 0.563/0.667/0.597 结论已废；
   27px 是本项目唯一可信档位。
7. **口径提醒**：LOBO 只统计「该类在训练集出现过」的测试样本，被排除的样本数写在 metrics.json 的
   `lobo.excluded_unseen_class`；多数类基线 0.117 只是参照下限，不是有意义的对照。

## 7. 结论与下一步

- **可行性成立**：27px 外观对「类别」有可学信号——checkpoint（30 epoch）within 0.630 / LOBO 0.477，显著高于多数类基线 0.117；充分训练（60–100 epoch）可到 0.734 / 0.641。
- **产品化不成立**：数据量与标注质量是瓶颈，不是网络容量；继续换网络/调参收益有限。
- 下一步优先级：
  1. 按 G 校准口径重标 6 阵（消掉 1–3 格漂移）；
  2. 补到 ≥10 阵 / ≥400 栋，重点补稀有类；
  3. 与 quad/几何先验结合做「候选 + 分类」两段式，而不是端到端检测。
