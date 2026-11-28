# ClashLab 桌面标注器 v1.8（Windows EXE，无需 Python）

## v1.8：重训流程修复 + 更强模型
- 事故：旧 train_hybrid_full 重训会使模型退化（召回 71%→13%）；已从 v1.7 EXE 恢复好模型并加质量闸门
- 新流程：label_qa → train_hybrid_final（复用 CV 流程）→ export_hybrid_onnx → 质量验证
- 新模型 b03 实测：标准 P84.0/R86.8/type97.5；多标 P75.7/R92.3；少错 P90.3/R71.4/type100
- 打包三档栋数：90 / 106 / 67（GT 91）
- EXE 106,487,761 bytes

## 用法
点四角 → 选模式（标准/多标/少错）→「自动预标注」→ 删误报/补漏 → 导出
