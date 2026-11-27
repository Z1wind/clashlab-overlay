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
