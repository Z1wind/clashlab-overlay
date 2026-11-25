# -*- coding: utf-8 -*-
"""视觉 token 中心（方案 A）：pages.py / draw.py 唯一取色来源。

口径：所有颜色给 RGBA 0..1 浮点（ImGui 直接用）；hex 仅文档对照。
禁止出现紫/靛蓝相（H 250°–295°）；主操作=绿系，次要=灰系，强调=琥珀。
本模块纯数据 + 纯函数，不建窗、不读盘、不写盘。
"""
from __future__ import annotations
import os

# ---------------------------------------------------------------- 色板（方案 A 锁定）
# 面板底板 #161A20，alpha 1.0 完全不透明（v6-B3：不许透光，整块纯色铺满面板矩形）
PANEL_BG = (0.086, 0.102, 0.125, 1.0)
PANEL_BORDER = (0.20, 0.24, 0.29, 1.0)

# 正文 #F4F7FA
INK = (0.957, 0.969, 0.980, 1.0)
# 次要 #BAC4CE alpha 0.92（不是 0.85）
SUB = (0.729, 0.769, 0.808, 0.92)
# 禁用文字
DIS_TXT = (0.482, 0.522, 0.576, 1.0)

# 唯一强调色 琥珀 #E8A33D；hover 提亮 #F2B65E；按下压暗
ACCENT = (0.910, 0.639, 0.239, 1.0)
ACCENT_HOVER = (0.949, 0.714, 0.369, 1.0)
ACCENT_PRESS = (0.796, 0.546, 0.204, 1.0)
# 琥珀底上的深字（选中页签用），禁止白字直接压琥珀
TAB_TEXT = (0.055, 0.067, 0.086, 1.0)

# 主操作绿 #197044（白字 5.74:1，实测）
PRIMARY = (0.098, 0.439, 0.267, 1.0)
# 语义
DANGER = (0.929, 0.380, 0.341, 1.0)
# 成功/已验证： muted 绿文字，禁用旧亮绿 (0.376,0.784,0.510)/(0.420,0.820,0.549)
SUCCESS = (0.557, 0.792, 0.627, 1.0)
WARN = (0.988, 0.808, 0.380, 1.0)

# rank 三档（只用于 3px 实色条 + ▲/◆/○ 形状 + 亮度分层；不铺行底）
RANK_R3 = (0.878, 0.357, 0.322, 1.0)   # #E05B52 最高威胁
RANK_R2 = (0.788, 0.604, 0.294, 1.0)   # #C99A4B 中威胁
RANK_R1 = (0.494, 0.576, 0.659, 1.0)   # #7E93A8 低威胁
RANK_GLYPH = {3: "▲", 2: "◆", 1: "○"}

# 次要按钮灰面（常态 / hover / 按下），1px 亮边
SEC_BG = (0.118, 0.145, 0.180, 1.0)       # #1E252E
SEC_BG_HOVER = (0.157, 0.188, 0.227, 1.0)  # #28303A
SEC_BG_PRESS = (0.086, 0.106, 0.137, 1.0)  # #161B23
SEC_BORDER = (0.30, 0.36, 0.43, 1.0)
# 禁用填充（整体 alpha 0.45）
DISABLED_BG = (0.055, 0.067, 0.086, 0.45)

# 选中行：2px 琥珀左竖条 + 底板提亮一档（#222833 vs 底板 #161A20）
SEL_BAR = ACCENT
SEL_ROW_BG = (0.172, 0.204, 0.243, 1.0)  # v6-C9 重修：选中底色抬一档，与未选 Δ≈22
ROW_BG = (0.094, 0.114, 0.145, 1.0)

# HUD 标签胶囊底 #05080F @0.72；文字 1px 黑描边
HUD_CAP = (0.020, 0.032, 0.058, 0.72)
HUD_STROKE = (0.0, 0.0, 0.0, 0.9)

# 编辑器画布 letterbox 底 / 网格线 / 标签胶囊（页面内，非面板底板）
CANVAS_BG = (0.020, 0.032, 0.058, 0.90)
GRID_LINE = (0.42, 0.48, 0.55, 0.30)
CHIP_BG = (0.02, 0.03, 0.06, 0.85)


# ---------------------------------------------------------------- 面板宽度
# 任务1：面板外置独立窗口，窗口即面板，panel_w=tw=440 固定；
# 旧的两套按客户区宽度算比例的公式已从代码删除，不留分支。
PANEL_W = 440.0


def panel_width(w: float) -> float:
    """固定面板宽 440（外置窗口即面板；旧比例公式已删）。"""
    return PANEL_W


# ---------------------------------------------------------------- 按钮三态
def _lift(rgba, factor):
    """RGB 通道乘 factor（clamp），alpha 保留。用于 hover 提亮 / 按下压暗。"""
    r, g, b, a = rgba
    return (min(1.0, r * factor), min(1.0, g * factor),
            min(1.0, b * factor), a)


def primary_states():
    """主按钮三态填充：常态 / hover(+8% 亮) / 按下(-12% 暗)。"""
    return {
        "normal": PRIMARY,
        "hover": _lift(PRIMARY, 1.08),
        "pressed": _lift(PRIMARY, 0.88),
    }


def secondary_states():
    """次按钮三态填充。"""
    return {
        "normal": SEC_BG,
        "hover": SEC_BG_HOVER,
        "pressed": SEC_BG_PRESS,
    }


def amber_states():
    """选中页签琥珀三态填充（C1：页签不许出现绿；唯一强调色琥珀）。"""
    return {
        "normal": ACCENT,
        "hover": ACCENT_HOVER,
        "pressed": ACCENT_PRESS,
    }


# ---------------------------------------------------------------- 开关
# PROBE 调试块开关：默认关；env CLASH_PROBE=1 才画（C10）。
PROBE_ENABLED = os.environ.get("CLASH_PROBE", "0") == "1"
# HUD 标签碰撞避让开关：默认关（主线验证 draw_important 期间不得挪标签）。
HUD_LABEL_AVOID = os.environ.get("CLASH_HUD_AVOID", "0") == "1"
