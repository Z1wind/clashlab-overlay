# ClashLab 桌面标注器 v1.6（Windows EXE，无需 Python）

## v1.6：预标注三种模式
- 顶部「模式：标准/多标/少错」循环切换
  - 标准：约 72 栋（平衡）
  - 多标：约 87 栋（召回优先，多删误报）
  - 少错：约 47 栋（精度优先，自己补更多）
- 模型同 v1.5（混合门控+特征比对），只是阈值不同
- EXE 106,486,384 bytes

## 验证（打包环境 smoke2，b03）
- standard n=72 / recall n=87 / precise n=47，均 ok=true
