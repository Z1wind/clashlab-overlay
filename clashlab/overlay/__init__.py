# -*- coding: utf-8 -*-
"""覆盖层 PANEL 模式包。

第一阶段（数据层 + 纯逻辑）：
  - data.py    数据加载与归一化（缺文件/坏 JSON 一律降级不崩）
  - editor.py  确认编辑器纯逻辑（命中测试、候选增删改、冻结产物生成）
  - pages.py   draw_panel(ctx, state) 签名骨架，UI 绘制待第二阶段

本包禁止在 import 阶段创建任何窗口、禁止启动 ImGui 后端。
"""
