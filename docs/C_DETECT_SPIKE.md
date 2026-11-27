# 检测器预研（C）结论：合成数据迁移失败（2026-11-27）

## 做了什么
- 合成检测数据集：`tools/build_detect_dataset.py`，ClashKing 立绘贴草地背景，1500 train / 240 val，46 类（**排除 firespitter/wall**）
- 训练：`tools/centernet_fast.py`（纯 torch CenterNet-mini，320px，17 类关键防御，12 epoch，RTX 4060）
- 推理：`tools/eval_centernet_fast.py` 跑真实战图 `out/live/enemy_scout_live.png`

## 结果（真实数据）
- 热图均值 **0.4915**、峰值 0.99 → 模型对整幅图都给出高置信，不是「检测到建筑」
- 真实图上取 30 个框，**全部错位**：把左上角 UI（SHADOW 名字/资源）、按钮、岩石背景都框出来（见 `out/live/detect_cf_eval.png`）
- 训练集 val 上 heatmap focal loss 从 0.56 降到 0.537（几乎不降），说明合成图内也没学到稳定特征

## 结论
**预注册判据（真实图命中 ≥60%）不达标，检测器方向停止。**
原因判断：合成背景与真实村庄域差距过大、立绘比例/遮挡/描边风格不同，加上 12 epoch 训练不足。

## 若要继续（需要新输入）
1. 真实截图 **人工框** 若干（≥200 栋）作训练/验证集——正好可用电脑标注器 `tools/annotate_web.py` 产出；
2. 或改「模板+几何约束」方案（已知阈值下不适用）；
3. 不建议继续用纯合成数据硬训。
