# 早晨简报（2026-11-28）

## 现在可以直接用
1. 装 dist/ClashLabAnnotator_20bases_v0.2.8.apk（md5 A1DE12AED7930E51CBA511BEF6DB9C69）
2. 点四角，可拖到图片外（拖到屏幕边缘会自动平移）
3. 双击放大、点「建筑：XX」选类型、点建筑中心
4. 「导出本张」自动跳下一张；标完 10 张点「导出全部」
5. 把 annot_all.json 发我，我跑一条命令训练：
   python tools/train_from_apk_export.py --export annot_all.json --epochs 12

## 通宵完成清单
- copy link 解码：确认不可行（且历史文档早有结论）
- 自动标注：模板匹配/格点分类器均证伪（与历史记录一致）
- APK：v0.2.6 四角可拖出图片、v0.2.7 边缘自动平移、v0.2.8 导出自动跳下一张（均真机验证）
- 工程：可移植构建脚本 + GitHub Actions 自动出包 + Release v0.3.7 + 训练一条命令

## 等你
- 政策风险改造是否启动（删 ADB 自动侦察 / 覆盖层降级 / 改名 / 去 Supercell 素材）
- 标注目标是否仍按先 10 张冲阶段 A