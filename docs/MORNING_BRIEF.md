# 早晨简报（2026-11-28）

## 一句话
标注 APK 打磨到 v0.3.0（真机验证），你标 10 张后我一条命令出准确率；自动标注路线已彻底证伪。

## 装哪个
dist/ClashLabAnnotator_20bases_v0.3.0.apk
8,325,422 bytes md5 E9EE6D9B2F95C36FD199116BBD46273E
https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.3.7

## 怎么标
1. 点四角（角在图外就往屏幕边缘拖，会自动平移）
2. 双击放大；点「建筑：XX」选类型
3. 点建筑中心；位置不准直接按住拖走
4. 「导出本张」自动跳下一张；左上角看已完成 N/20
5. 标完 10 张 →「导出全部」→ 把 annot_all.json 发我

## 你发来后我跑
python tools/train_from_apk_export.py --export annot_all.json --epochs 12
（自动留一基 CV，输出 top1/top3，保存 models/apk_type_cls.pt）

## 通宵做成了什么
- APK 7 个版本迭代，全部真机/无头验证：短屏适配、缩放平移、角点出图、边缘自动平移、沿上张四角、导出自动跳、进度、拖动建筑
- GitHub Actions 自动出包 + 可移植构建脚本 + Release v0.3.7（含 APK 与桌面端）
- copy link 不可解码、自动标注不可行的证据与结论（避免以后重复研究）

## 等你拍板
1. 政策风险改造是否启动（删 ADB 自动侦察 / 覆盖层降级 / 改名 / 去 Supercell 素材）
2. 标注目标是否仍按先 10 张冲阶段 A