# 新标注到位后的一键重训流程

## 1. 收集标注
把标注 App / 桌面版导出的 `annot_*.json` 放到任意目录（例如 `Downloads`）。

## 2. 质检（必须先过）
```powershell
python tools/label_qa.py --labels "路径1.json;路径2.json;..."
```
- 输出 PASS / WARN / FAIL；FAIL 的图不要进训练（对齐 ratio < 1.2 视为标偏）

## 3. 重训混合模型 + 导出 ONNX
```powershell
$env:CLASHLAB_EXPORTS = "路径1.json;路径2.json;..."
python tools/train_hybrid_full.py          # 训练门控 + embedding + 原型
python tools/export_hybrid_onnx.py         # 导出 ONNX 并校验
Remove-Item Env:\CLASHLAB_EXPORTS
```

## 4. 重建桌面 EXE（如需要）
```powershell
powershell -File tools/build_v16.ps1       # 生成 dist_exe/ClashLabAnnotator.exe
python tools/package_v17.py                # 复制到 dist/ 并更新文档
```

## 5. 验证
- `python tools/preannotate_test.py`（b03 单图）或 `tools/retest_preannotate.py`
- 打包环境 smoke：`powershell -File tools/smoke_v16.ps1`（三档模式栋数）

## 当前基线（8 张标注）
- 混合方案 CV：P62.3% / R71.0% / F1 .658 / 类型 91.8%
- 实际 b03（训练集内）：标准 P90.3/R71.4/type 100%
- 类型分类器（8 张 CV）：top1 95.4% / top3 98.2%

## 经验
- 10–20 张：预期 F1 0.70–0.75；20–30 张：0.75–0.82；40+ 张可考虑换 heatmap 检测器
- 新图务必与已有图同源（同一网站渲染、同视角），不要混入游戏截图（域差异会掉点）