# 真实标注训练结果（2026-11-28）

## 数据
- 用户导出 8 张（Downloads/annot_b01..b08.json），每张 89-94 栋、33-36 类
- 全部 8 张：729 样本 / 38 类

## 结果 A：8 张全用（留一基）
- mean top1 = 0.445，top3 = 0.71（基础版 14 epochs）
- 增强版（112px+颜色/几何增强+类平衡+cosine）：mean top1 = 0.591，top3 = 0.710
- 但 b01 top1=8.5%、b02=7.5%，其余 38%-87%

## 结果 B：排除 b01/b02（6 张留一）
- mean top1 = 0.882，top3 = 0.948
- 各折：0.934 / 0.876 / 0.692 / 0.923 / 0.944 / 0.922

## 分类型（6 张 CV）
- 100%：town-hall / eagle-artillery / air-defense / wizard-tower / archer-tower / bomb-tower / gold-storage / elixir-storage / pet-house / hero-hall / blacksmith 等
- 83-92%：monolith / ricochet-cannon / x-bow / multi-archer-tower / mortar / inferno-tower / cannon / hidden-tesla / builder-hut
- 偏低：spell-tower 0.73 / helper-hut 0.67 / dark-barracks 0.60

## b01/b02 的问题（诊断）
- 两张标注的裁剪里建筑多在边缘：落点不在建筑中心（疑似标偏）
- b01 缺 town-hall / builder-hut / laboratory / pet-house 等关键类型；b02 类型齐但仍偏
- 8 种镜像/转置变换都无法救回 → 不是坐标系问题，是数据本身问题

## 结论
- 能训练，而且 6 张好数据就能到 88%；把 b01/b02 重标（或再补 2-4 张好数据）预计到 90%+
- 产物：models/apk_type_cls_aug6.pt（模型）、out/apk_type_report_aug6.json（报告）
