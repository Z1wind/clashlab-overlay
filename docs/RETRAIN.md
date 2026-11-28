# 新标注到位后的一键重训流程

> 2026-11-29 更新：当前基线 = 18 张标注（v2.1）

## 1. 质检（必须先过）
```powershell
python tools/label_qa.py --labels "路径1.json;路径2.json;..."
```
- PASS 才进训练；FAIL（align<1.2）的图要重标

## 2. 重训混合模型（全量）
```powershell
$env:CLASHLAB_EXPORTS = "a.json;b.json;..."
python tools/train_hybrid_final.py
python tools/export_hybrid_onnx.py
Remove-Item Env:\CLASHLAB_EXPORTS
```

## 3. 质量闸门
```powershell
python tools/retest_preannotate.py
```
- 标准档 pred 应 >= 50 且 P >= 80%；不达标从 `models/_good_v20` / `models/_good_before_retrain` 回滚

## 4. 打包 + 发布
```powershell
powershell -File tools/build_v20.ps1
python tools/package_v21.py
python tools/upload_exe21.py
```

## 5. 验证（交付前必做）
- `tools/smoke_v16.ps1`：三模式 + 补充预标注栋数
- `tools/verify_v21_final2.py`：Range GET 206 + 首 MB md5 + asset digest vs 本地 sha256

## 当前基线（v2.1，18 张标注）
- b03 训练集内：标准 P91.8/R85.7/type98.7；多标 P84.8/R92.3；少错 P94.2/R71.4
- EXE：106,491,120 bytes，sha256 082b7cb8…
- 18 折诚实 CV：运行中（前 5 折 F1 0.667/0.729/0.709/0.671/0.498）

## 数据量经验
- 8 张：CV F1 0.658
- 18 张：预计 0.70 左右（CV 进行中），b03 精度 +7.8pt
- 目标 30 张：预计 F1 0.75+；40+ 张可考虑 heatmap 检测器