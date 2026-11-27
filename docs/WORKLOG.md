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
