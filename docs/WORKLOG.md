# WORKLOG

## 通宵轮次 1（2026-11-28 01:27-02:00）

### P0 官方 copy link 解码 —— 已排除（有证据）
- 页面含 `link.clashofclans.com/en?action=OpenLayout&id=TH16:WB:AAAA...`（war_138 实测）
- URL 解码 base64 后仅 24 字节：00 00 00 10 00 00 00 02 + 16 字节哈希 → 服务端引用，不含建筑坐标
- 页面无内嵌布局数据（无 buildings/coords/tiles；coord-like pairs = 0）→ 该路线放弃

### 20 张图与来源 id 映射 —— 恢复成功（20/20）
- `out/layouts_src/mapping.json`：b01=war_138, b02=war_143, b03=war_141, b04=war_139, b05=defence_17, b06..b20=war_144/142/140/1..9/defence_84/85/86

### 关键发现：5 张手工标注的 GT 坐标相对图片整体偏移 1-2 格
- 用 01_annotated 的 quad 把 86 个 GT 画到 b01：红圈不在建筑上（`out/layouts_src/gt_check_b01.png`）
- 枚举 quad 角点顺序无效（Calib.from_quad 内部 order_diamond 会重排）
- 缩放/平移/旋转粗优化仅轻微改善；局部模板匹配 13 锚点 + from_anchors 单应后中心区改善、边缘仍偏
- 含义：现有 render GT 不能直接用于训练，需先 RANSAC 锚点校正或重新标定

### 尝试过的自动识别（负面结果）
- ClashKing 立绘全图模板匹配：243 检测 / TP=0（匹配到森林纹理）→ 不可用
- 渲染图格点分类器（4 基训练 / defence17 验证）：塌缩到全背景（召回 0）
- 平衡采样+背景降权重训：在 0-1 之间震荡，未收敛

### 下一轮计划
1. RANSAC 锚点拟合，校正 5 张 GT 的 quad
2. 校正成功 → 重新生成 GT → 训练格点分类器 → 留出验证
3. 仍失败 → 人工半自动校准 + 逐张视觉标注（慢但可靠）

## 通宵轮次 3（2026-11-28 02:20-02:40）

### CI 构建 APK —— 已接入并跑通
- 新增可移植构建脚本 tools/build_apk_ci.py（读 JAVA_HOME/ANDROID_HOME，Win/Linux 通用）
- 新增 .github/workflows/build-apk.yml（JDK17 + Android SDK 34，构建并上传 artifact），推送即触发
- GitHub API 推送可行，run 1989763a 成功
- 发现 CI artifact 仅 55KB：根因是 20 张阵图被 .gitignore 第 61 行 android/assets/img/ 忽略、仓库中不存在
  -> 已 git add -f 20 张图并推送（commit 52ee008），CI 自动重跑（run 52ee008b）

### Release v0.3.7
- 已创建，资产：APK v0.2.5（8,292,385）+ units.html + 样例包 v2 + ClashOverlay.exe

### 待办
- 确认新 CI 构建 APK 尺寸恢复约 8.3MB 并校验 md5
- 登记验证 + 早晨简报
### 轮次 3 补充：CI 产物校验（通过）
- run 52ee008b 成功；artifact 8,291,484 B；解包 APK 8,296,541 B，含 20 张图
- CI 内 annotate6.html md5 与本地一致（差异仅 Linux/Windows zip 元数据 ~4KB）
- Release v0.3.7 资产四项尺寸与本地一致；APK 下载 md5 与本地一致

## 通宵轮次 4-5（2026-11-28 02:40-03:10）

### APK v0.2.6：四角可以拖出图片边界
- 用户反馈：APK 不能像最初 HTML 那样把角拉到截图外
- 根因：角点归一化坐标被 clamp 在 0..1
- 修复：画布按舞台比例留 6% 边距，角点允许 -0.25..1.25；fitCanvas 改为舞台相对
- 图片保持约 88% 舞台大小（横向可伸出约 11 格，纵向约 2.7 格）
- 无头浏览器自测：off=326,39 wh=1245x572 outside=[-0.2,0.5] ok=true
- 模拟器真机导出：corners_norm 含 -0.016 / 1.039，HAS_OUTSIDE=True
- 产物：dist/ClashLabAnnotator_20bases_v0.2.6.apk 8,300,644 bytes md5 FEEEAD7CC47722E1F087DF35075666CB
- Release v0.3.7 资产已替换并校验 md5；提交 ef0b608

### 数据集流水线兼容外部角点
- tools/apk_export_to_dataset.py 支持 corners_norm 为负/超过 1（warpPerspective 采样边界外为黑）
- tests/test_apk_export_dataset.py 新增：外部角点不崩溃、bundle 导出解析；3 项测试 OK

## 通宵轮次 6-8（2026-11-28 03:10-04:05）

### APK v0.2.7 / v0.2.8
- v0.2.7：拖角到屏幕边缘自动平移（真机实测拖到顶边后 corners_norm[0]=[0.024,-0.6]，MIN_Y=-0.6）
- v0.2.8：导出成功后自动跳到下一张未标定的图（真机 1/20 -> 2/20）
- 当前产物：dist/ClashLabAnnotator_20bases_v0.2.8.apk 8,308,903 bytes md5 A1DE12AED7930E51CBA511BEF6DB9C69

### 训练流水线（一条命令）
- 新增 tools/train_from_apk_export.py：APK 导出 JSON -> crops -> 训练 CNN -> 留一基 top1/top3 -> 保存 models/apk_type_cls.pt
- 烟测：01_annotated 转 v2 导出，86 crops / 31 类，训练+保存通过（单基无法留一评估，多基后自动 CV）

### 历史结论去重（重要）
- docs/BASELINK_RESEARCH.md 早已写明 copy link 不可离线解码（24B 服务端引用）——本轮 r1 又验证了一次，后续不要再试
- docs/AUTO_ANNOTATE_FAIL.md 已记录自动标注失败（无背景类、滑窗假阳性），本次模板匹配 TP=0 再次印证

### 多基留一 CV 烟测（用历史 5 张标注）
- 391 crops / 31 类；留一基 top1 分别为 0.058 / 0.053 / 0.104 / 0.066 / 0.105，mean top1 = 0.077
- 结论：流水线机械上跑通；准确率低是因为历史标注整体偏移（裁剪不含目标建筑），与 r1 的对齐诊断一致
- 等用户用 v0.2.8 新标 10 张（四角目视对齐）后重跑，预期显著提升
- 产物：out/apk_type_report_cv.json、models/apk_type_cls_cv.pt

## 通宵轮次 9-10（2026-11-28 04:05-04:35）

### APK v0.2.9：总进度显示
- 左上角「第 X/20 张 · 已完成 N」；真机：0 → 1 → 导出后跳第 2 张
- 产物 md5 6B640BC2008DADDC90DE8F92321DA237

### APK v0.3.0：已放建筑可拖动
- 靠近已放建筑按住即可拖到正确格子（不用删了重放）
- 无头浏览器自测：before=[18,18] after=[23,22] changed=true
- 产物：dist/ClashLabAnnotator_20bases_v0.3.0.apk 8,325,422 bytes md5 E9EE6D9B2F95C36FD199116BBD46273E

### 通宵总结（轮次 1-10）
- P0 copy link 解码：证伪（且历史文档早有结论）
- 自动标注：模板匹配/格点分类器均证伪（与历史记录一致）
- APK：v0.2.3 短屏适配 → v0.2.5 沿上张四角/双击/全清空 → v0.2.6 角点出图 → v0.2.7 边缘自动平移 → v0.2.8 导出自动跳 → v0.2.9 进度 → v0.3.0 拖动建筑
- 工程：可移植构建 + GitHub Actions + Release v0.3.7 + 训练一条命令 tools/train_from_apk_export.py
- 待用户：标 10 张发 annot_all.json；政策风险改造待批准

## 通宵轮次 11（2026-11-28 04:35-04:50）：尺度感知锚点校正（失败，记录）

- 思路：按 footprint 推算立绘显示尺寸，只在旧标注预测位置 ±2 格搜索匹配，再 RANSAC 拟合 quad
- 结果：82/86 个锚点被接受（阈值 0.80），RANSAC 内点 19，但叠加图显示红圈仍落在草地/墙上（out/layouts_src/scale_anchor_b01.png）
- 结论：历史 5 张渲染图的标注本身不可信（类型与位置都可能错），无法通过几何校正救回；后续不要再在旧标注上做自动标注
- 唯一可靠路线：用户用 APK v0.3.0 目视标注 → annot_all.json → tools/train_from_apk_export.py

### 通宵收尾
- 目标状态：APK v0.3.0（真机验证）、训练一条命令、CI/Release 完成；自动标注与 copy link 均证伪
- 等用户：标注 10 张 + 政策改造批准

## 用户 8 张标注训练（2026-11-28 16:10）
- 8 张全用 CV top1 59.1%（增强）/44.5%（基础）；b01/b02 异常低
- 排除 b01/b02：6 张 CV top1 88.2% / top3 94.8%
- b01/b02 诊断：落点偏移、b01 缺关键类型；镜像/转置无法修正
- 产物：models/apk_type_cls_aug6.pt、out/apk_type_report_aug6.json、docs/TRAIN_RESULT_20261128.md

## 训练与预标注交付（2026-11-28 16:30-17:30）
- 类型分类器升级：112px/40轮 CV top1 91.0% / top3 96.7%（models/apk_type_cls_s112e40.pt）
- 自动找位置：单阶段扫描器 P32.5/R64.1/F1 .42 → 两阶段门控 P61.1/R73.7/F1 .645
- 完整流水线诚实 CV：P71.5 / R45.6 / type_acc 87.4%；ONNX 推理 2.3-4.2s/张
- 桌面版 v1.3：内置 ONNX 模型 + 「自动预标注」按钮；打包环境 smoke n=72 / 4201ms
- 产物：dist/ClashLabAnnotator_Desktop_v1.3.exe 106,311,382 bytes md5 C5A1985C67A688404D467EFE68F659AF
- Release v0.3.7 资产已上传并校验；git 提交 72e7afd（清理 dist_exe/build_exe 误入库）

## 用户思路验证：关键贴图直接比对（2026-11-28 18:20）
- 方案：拿已标建筑 4x4 窗口裁片当模板（每类最多 6 个），全图逐格 NCC 匹配 + 阈值扫描 + 距离去重
- 全类型结果：prec 0.290 / recall 0.525 / f1 0.364 / type_acc 0.707（差于 CNN 流水线 P0.715/R0.456/F1 0.545）
- 仅外形独特 13 类：prec 0.328 / recall 0.255 / f1 0.233（TH/EA/法术塔等命中时类型 100%，但误报极多）
- 结论：原始像素 NCC 对视角/缩放/相邻建筑/等级变化不鲁棒，直接贴图比对打不过 CNN
- 可行升级：用度量学习（embedding + 最近邻）代替原始 NCC，让「同类型不同基」聚在一起，再做比对
- 产物：out/template_match_report.json、out/template_distinctive_report.json、tools/template_match_eval.py、tools/template_distinctive_eval.py

## 用户思路（先1后2）结果（2026-11-28 19:10）
- 数据更新：重标 b01/b02 后全 8 张可用（b01 90 栋 / b02 92 栋，纹理能量接近正常）
- 分类器 8 张 CV：top1 95.4% / top3 98.2%
- 方案1 embedding(ArcFace)+背景类 最近邻：P44.7 R71.4 F1 .540 type 96.3%
- 方案2 混合（CNN 门控 + embedding 最近邻/背景校验）：P62.3 R71.0 F1 .658 type 91.8% ← 当前最佳
- 对比软分类流水线：P70.4 R53.2 F1 .597 type 83.1%
- 结论：用户「特征比对」思路在「门控 + 学习特征最近邻」组合下有效：召回 53→71（+18pt）、类型 83→92（+9pt），精度让 8pt

## 方案3：混合 + 独特外形贴图二次校验（2026-11-28 19:25）
- 在混合方案上加「13 种独特外形建筑的贴图 NCC 校验」，阈值与 t3 一起网格搜索
- 结果：P51.4 / R63.8 / F1 .564 / type 80.0%（差于混合 P62.3/R71.0/F1 .658）
- t3=0（即不启用贴图校验）在 8 折中被选 4 次；fold5 出现退化（pred=0），拉低均值
- 结论：贴图二次校验对混合方案没有稳定增益，保持 v1.5 混合方案（已交付）
- 脚本：tools/train_hybrid_tpl_cv.py；报告：out/hybrid_tpl_report.json

## 持续实验（2026-11-28 20:00-20:20）
- 分类器多seed集成+TTA：top1 94.1%（单模型 95.4%），TTA 无变化 → 不采用
- 混合变体（修正偏移后重评，leaky）：位置精修 F1 .723→.739；TTA/占用后处理变差；诚实 CV 前4折精修 0.671 vs 基线 0.686 → 精修无增益，已停
- 更强数据增强（透视+遮挡+颜色）：CV P56.3/R69.3/F1 .613/type 93.8 vs 基线 .658 → 增强过强有害，不采用
- 结论：当前混合基线（P62.3/R71.0/F1 .658/type 91.8）仍最优；真正的提升来自 v1.7 的裁剪中心 bug 修复

## 实验：门控 6x6 上下文（2026-11-28 20:25）
- 门控看 6x6 格上下文（其余同混合方案），前 6 折 F1 0.622/0.626/0.663/0.601/0.525/0.559
- 对比基线 4x4：0.616/0.726/0.766/0.636/0.738/0.711 → 更差，已终止
- 结论：4x4 上下文足够；当前最优仍是混合基线 + v1.7 裁剪修复

## 实验：网格分割检测器原型（2026-11-28 20:35）
- 方案：四角规范化 512x512 输入 → U-Net → 44x44 类型图（一次前向替代 1600 次滑窗）
- 8 基留一结果：prec 0.368 / recall 0.103 / f1 0.159 / type 0.843
- 结论：8 张数据远不足以训分割检测（稀疏正样本 + 过拟合）；需 40+ 张再试，当前不采用
- 脚本：tools/train_grid_seg_cv.py；报告：out/grid_seg_report.json

## 标注质检工具 label_qa.py（2026-11-28 20:40）
- 检查：version/corners/图片存在/建筑数/tile 范围/重复/缺类型/对齐 ratio（标注点纹理能量 vs 随机位置）
- 当前 8 张全部 PASS，对齐 ratio 2.53-4.00（b01/b02 重标后 3.20/3.05，修复前仅 ~1.0-1.2）
- 后续用户新标注可直接跑：python tools/label_qa.py --labels "a.json;b.json"

## 实验：硬负样本门控（2026-11-28 20:40）
- 负样本 50% 取建筑周围 2.2-4.5 格环带（墙/装饰），其余随机
- 8 基 CV：P62.1 / R64.8 / F1 .625 / type 92.5%（基线 P62.3/R71.0/F1 .658）→ 无增益
- 实验脚本：tools/train_hybrid_hardneg_cv.py；报告：out/hybrid_hardneg_report.json

## 平台期总结（8 张数据，共验证 8 组方案）
- 负结果：分类器集成/TTA、强增强、位置精修、占用后处理、6x6 上下文、硬负样本、网格分割检测器
- 正结果：v1.7 裁剪中心 bug 修复（实际精度 62%→90%，b03）
- 结论：数据量是唯一瓶颈；需要更多标注（目标 20-30 张）才能继续提升

## 阈值/NMS 调优（2026-11-28 21:15）
- 阈值网格 CV（8 折）：当前 standard(0.85/0.85) P.648/R.630/F1 .639；最优 F1 在 (0.70/0.85) P.608/R.688/F1 .645（仅 +0.006，暂不改）
- recall 模式 (0.70/0.70)：P.484/R.795（召回最高，误报多）
- NMS 去重系数扫描（leaky 8 基准）：0.70/0.85/1.00 会残留重复框（pred 134-141），1.15 最佳 F1 .774/pred 86，1.30 略降 → 保持 1.15
- 结论：v1.8 参数已接近当前数据的最优，无需再发版
- 产物：out/mode_threshold_grid.json、out/logs/nms_sweep.log、tools/tune_modes_cv.py、tools/nms_sweep.py

## 实验：半格相位候选合并（2026-11-28 21:25）
- leaky 8 基准：整数格 P81.5/R75.2/F1 .780；半格 P82.5/R75.2/F1 .783；合并 P80.4/R82.3/F1 .811（方向性 +3pt）
- 诚实 8 折 CV：合并后 P69.3/R62.2/F1 .643/type 95.0（基线 P62.3/R71.0/F1 .658/type 91.8）
- 结论：半格合并能提精度 +7pt、类型 +3pt，但召回 -9pt、F1 略降；暂不替换标准档，保留为「精确档」可选方案
- 代码已预留 preannotate_core.detect(phases=(0.0,)) 参数，可随时启用
- 脚本：tools/half_offset_scan.py、tools/train_hybrid_halfphase_cv.py、tools/mk_halfphase_cv.py

## v1.9 交付前全基准一致性检查（2026-11-28 21:40，leaky）
- standard: P81.5 / R75.2 / type98.1 / 平均84栋 / 2.6s
- recall:   P72.0 / R79.8 / type96.9 / 平均103栋 / 2.6s
- precise:  P86.5 / R73.4 / type99.1 / 平均77栋 / 5.1s
- 最弱项：b07 standard R0.61；b05 recall P0.50（误报多）→ 后续数据补 b05/b07 类分布
- 脚本 out/logs/v19_allbases.log、tools/eval_v19_allbases.py

## 类型级错误分析 + 发布脚本（2026-11-28 21:45）
- 最差召回（leaky 8 基准，标准档）：dark-elixir-drill 0.48、barracks/spell-factory/dark-spell-factory/pet-house 0.50、elixir-collector 0.54、elixir-storage 0.56、gold-mine 0.62
- 类型混淆极少：builder-hut<->helper-hut x5+2、scattershot->builder-hut x1、army-camp->mortar x1
- 结论：瓶颈是「小建筑密集排布时的门控漏检」，不是分类；新标注优先补收集器/储藏/训练营密集阵
- 标准档阈值 leaky 扫描确认最优：(0.85/0.85) P.815/R.752/F1 .782；降阈值只换 +0.4pt 召回、丢 1.5pt 精度
- 新增 tools/release_from_labels.ps1：一条命令 = 质检->重训->质量闸门(失败回滚)->打包->上传；语法校验通过（未跑全流程，等新数据）

## 18 张标注重训 + v2.1 发布（2026-11-29 00:15）
- 用户新提供 b10/b11/b12/b14/b15/b16/b17/b18/b19/b20 共 10 张（缺 b09/b13，不影响）
- label_qa：10/10 PASS（bld 88-93，types 33-36，align 1.97-3.08）
- 全量 18 张重训（train_hybrid_final.py）：b03 训练集内 标准 P91.8/R85.7/type98.7；多标 P84.8/R92.3；少错 P94.2/R71.4
- 对比 8 张版：标准 P84.0→91.8（+7.8pt），召回持平 → 误报明显减少
- v2.1 EXE：106,491,120 bytes md5 10B01A3F3FC15781B9082CC093DF26EE sha256 082b7cb8…77b780（Release digest 一致）
- 打包 smoke：标准 85 / 多标 100 / 少错 77；补充预标注 existing=10 → 75
- 18 折诚实 CV 进行中（前 3 折 F1 0.667/0.729/0.709，均值 0.702 vs 8 张 .658）
- 旧模型备份：models/_good_v20（可回滚）
