# -*- coding: utf-8 -*-
"""覆盖层配置：config/overlay.json 的加载、合并默认值与热键表。

运行时线（A）独占创建与写入本文件；面板线只读展示，新增键写
out/overlay/needs_config_hotkeys.md，由运行时合并。
"""
from __future__ import annotations

import json
import os

DEFAULTS = {
    # false = 不可见自检模式（touch_report.md 出现前默认）；true = 可见覆盖层
    "show": False,
    # 热键表：action 为运行时内部动作；UI 只读展示
    "hotkeys": {
        "mode_toggle": "F8",      # HUD <-> PANEL
        "farm_toggle": "F9",      # 采集一键启停请求
        "reload": "F12",          # 重新加载数据（mtime 侦测）
        "live_toggle": "F7",      # live / dry-run 切换
        "escape_hud": "ESC",      # 回 HUD 并中断待执行动作
    },
    # 手工贴合偏移（物理像素），由运行时保存，UI 不回写
    "offset": {"dx": 0, "dy": 0},
    # PANEL 外置位置：right=客户区右侧外 / down=客户区下方 / inner=叠游戏内右侧
    "panel_position": "right",
    # 自检模式退出秒数（show=false 时）
    "self_check_seconds": 30,
    # 帧率统计窗口
    "fps_window": 180,
    # False=跟随前台（雷电不在前台即隐藏）；True=常显（仅取证用）
    "always_on_top": False,
    # 主屏禁区守卫：False=渲染窗口在主显示器时强制隐藏（默认，硬底线）；
    # True=逃生开关，不建议使用
    "allow_primary": False,
}

# 热键名 -> ImGui 键码（轮询 io.keys_down 边沿用；名字仅供展示）
HOTKEY_ALIASES = {
    "F1": "f1", "F2": "f2", "F3": "f3", "F4": "f4", "F5": "f5", "F6": "f6",
    "F7": "f7", "F8": "f8", "F9": "f9", "F10": "f10", "F11": "f11", "F12": "f12",
    "ESC": "escape",
}


def config_path(root: str) -> str:
    return os.path.join(root, "config", "overlay.json")


def load_overlay_config(root: str) -> dict:
    """读 config/overlay.json，缺失/损坏 -> 默认值；深合并。"""
    cfg = json.loads(json.dumps(DEFAULTS))
    path = config_path(root)
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            _merge(cfg, raw)
    except FileNotFoundError:
        pass
    except Exception:
        # 损坏不崩，落默认
        pass
    return cfg


def save_overlay_config(root: str, cfg: dict) -> None:
    """运行时独占写入 config/overlay.json。"""
    path = config_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _merge(base: dict, over: dict) -> None:
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
