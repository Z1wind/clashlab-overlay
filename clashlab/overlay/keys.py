# -*- coding: utf-8 -*-
"""绑键数据层：动作表 / VK 映射 / 持久化 config/overlay_keys.json。

纯逻辑：不 import imgui、不建窗、不写 UI；运行时轮询与设置页共用。

键名规范（小写存储）：f1–f12 / esc / tab / space / enter / a–z / 0–9。
冲突规则：不允许两个动作共用同一键，冲突必须拒绝；雷电自身占用键
（f8 录屏 / f9 操作录制 / f11 全屏）允许坚持绑定，但写盘时记录警示。

持久化：config/overlay_keys.json（UTF-8）。读失败 / 字段缺失一律回退默认
并记一条 warn，绝不抛异常把覆盖层带崩。
"""
from __future__ import annotations

import json
import os

# ---------------------------------------------------------------- 动作表
# id: 运行时内部动作；zh: 面板设置页中文名；key: 默认键；desc: 说明
# 默认键已避开雷电热键（F8 录屏 / F9 操作录制 / F11 全屏）。
ACTION_DEFS = [
    {"id": "toggle_mode", "zh": "切换面板", "key": "insert",
     "desc": "HUD <-> PANEL 切换"},
    {"id": "capture", "zh": "采集一帧", "key": "delete",
     "desc": "开始/停止采集请求"},
    {"id": "live", "zh": "Live 跟随", "key": "f7",
     "desc": "live / dry-run 切换"},
    {"id": "reload", "zh": "重载情报", "key": "f12",
     "desc": "重新加载阵型/情报数据"},
    {"id": "back_hud", "zh": "回 HUD", "key": "esc",
     "desc": "返回 HUD 穿透模式"},
]

# 雷电模拟器自身占用键（F8=录屏 / F9=操作录制 / F11=全屏）：允许坚持绑定但警示
RESERVED_LD = {
    "f8": "录屏",
    "f9": "操作录制",
    "f11": "全屏",
}

# Win32 VK 表（F1–F12=0x70..0x7B，ESC=0x1B，TAB=0x09，SPACE=0x20，ENTER=0x0D；
# INSERT=0x2D（非扩展键），DELETE=0x2E（扩展键，注入须带 KEYEVENTF_EXTENDEDKEY）；
# 字母取大写 ord，数字取 ord）
_VK_F_BASE = 0x70  # F1
_VK = {
    "esc": 0x1B, "tab": 0x09, "space": 0x20, "enter": 0x0D,
    "insert": 0x2D, "delete": 0x2E,
}

# 反向表：VK -> 规范键名（捕获轮询用）
_VK_FROM = {}
for _n in range(1, 13):
    _vk = _VK_F_BASE + _n - 1
    _VK[f"f{_n}"] = _vk
    _VK_FROM[_vk] = f"f{_n}"
for _name, _vk in _VK.items():
    _VK_FROM[_vk] = _name
for _ch in "abcdefghijklmnopqrstuvwxyz":
    _VK[_ch] = ord(_ch.upper())
    _VK_FROM[ord(_ch.upper())] = _ch
for _ch in "0123456789":
    _VK[_ch] = ord(_ch)
    _VK_FROM[ord(_ch)] = _ch

# 捕获轮询扫描的 VK 全集（小表，每帧只在捕获态扫描）
WATCH_VKS = sorted(_VK_FROM.keys())

# 模块内会话态：load(root) 载入后，set_key/clear_key/reset 在内存态上操作并落盘
_STATE = {"root": None, "bindings": {}, "warnings": {}, "mtime": 0.0, "warns": []}


# ---------------------------------------------------------------- 基础工具

def bind_path(root: str) -> str:
    return os.path.join(root, "config", "overlay_keys.json")


def normalize_key(name):
    """规范键名；非法返回 None。接受大小写/空格，统一小写。"""
    if not isinstance(name, str):
        return None
    k = name.strip().lower().replace(" ", "")
    if k in _VK:
        return k
    return None


def vk_of(key):
    """规范键名 -> Win32 VK；非法返回 None。"""
    k = normalize_key(key)
    return _VK.get(k) if k else None


def key_from_vk(vk: int):
    """VK -> 规范键名；未登记返回 None。"""
    return _VK_FROM.get(int(vk))


def display(key) -> str:
    """面板展示名：f8->F8，esc->ESC，space->SPACE，字母数字原样大写。"""
    k = normalize_key(key)
    if not k:
        return "未绑定"
    if k.startswith("f") and k[1:].isdigit():
        return k.upper()
    return k.upper()


def default_bindings() -> dict:
    return {d["id"]: d["key"] for d in ACTION_DEFS}


def action_def(action_id: str):
    for d in ACTION_DEFS:
        if d["id"] == action_id:
            return d
    return None


def reserved_hint(key) -> str:
    """雷电占用键提示；非占用返回空串。"""
    k = normalize_key(key)
    if k in RESERVED_LD:
        return f"该键雷电也占用（{RESERVED_LD[k]}），可能同时触发"
    return ""


# ---------------------------------------------------------------- 载入 / 落盘

def load(root: str) -> dict:
    """载入 config/overlay_keys.json，合并默认绑定；失败回退默认并记 warn。

    返回 {action_id: key}；warnings 另存会话态，可用 pop_warns() 取一次性 warn。
    任何异常都不抛出。
    """
    _STATE["root"] = root
    merged = default_bindings()
    warns: dict = {}
    path = bind_path(root)
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            ks = raw.get("keys") or {}
            for d in ACTION_DEFS:
                v = ks.get(d["id"])
                if normalize_key(v):
                    merged[d["id"]] = normalize_key(v)
            w = raw.get("warnings") or {}
            if isinstance(w, dict):
                warns = {str(k): str(v) for k, v in w.items() if v}
        _STATE["mtime"] = os.stat(path).st_mtime
    except FileNotFoundError:
        _STATE["warns"].append("overlay_keys.json 缺失，已回退默认绑键")
    except Exception as e:  # 损坏/非法类型：绝不崩
        _STATE["warns"].append(f"overlay_keys.json 读取失败（{e}），已回退默认绑键")
    _STATE["bindings"] = merged
    _STATE["warnings"] = warns
    return dict(merged)


def save(root: str | None = None) -> None:
    """把会话态写盘；root 缺省用上次 load 的根。目录缺失自动建。"""
    root = root or _STATE["root"]
    path = bind_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc = {
        "version": 1,
        "keys": {d["id"]: _STATE["bindings"].get(d["id"]) or "" for d in ACTION_DEFS},
        "warnings": _STATE["warnings"],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2, sort_keys=True)
    try:
        _STATE["mtime"] = os.stat(path).st_mtime
    except OSError:
        pass


# ---------------------------------------------------------------- 查询 / 写入

def conflict(action_id: str, key, bindings=None):
    """占用该键的其它动作 id；无冲突返回 None。排除 action_id 自身。"""
    k = normalize_key(key)
    if not k:
        return None
    store = bindings if bindings is not None else _STATE["bindings"]
    for aid, v in store.items():
        if aid != action_id and normalize_key(v) == k:
            return aid
    return None


def _reserved_warn_text(key) -> str:
    return reserved_hint(key)


def set_key(action_id: str, key) -> tuple[bool, str, str]:
    """绑定 action_id 到 key。

    返回 (ok, kind, msg)：kind ∈ red/yellow/green。
    冲突 -> (False, 'red', '已被 <动作名> 占用')，原绑定不变；
    雷电占用 -> (True, 'yellow', 警示)，写入并把警示记进 warnings；
    成功 -> (True, 'green', '已保存 overlay_keys.json')。
    """
    if not action_def(action_id):
        return False, "red", "未知动作"
    k = normalize_key(key)
    if not k:
        return False, "red", "无效键名"
    other = conflict(action_id, k)
    if other:
        other_def = action_def(other)
        name = other_def["zh"] if other_def else other
        return False, "red", f"已被 {name} 占用"
    _STATE["bindings"][action_id] = k
    hint = _reserved_warn_text(k)
    if hint:
        _STATE["warnings"][action_id] = hint
    else:
        _STATE["warnings"].pop(action_id, None)
    save()
    if hint:
        return True, "yellow", hint + "；已保存"
    return True, "green", "已保存 overlay_keys.json"


def clear_key(action_id: str) -> tuple[bool, str, str]:
    """清除绑定（未绑定动作不再进 vk_map）。"""
    if not action_def(action_id):
        return False, "red", "未知动作"
    _STATE["bindings"][action_id] = ""
    _STATE["warnings"].pop(action_id, None)
    save()
    return True, "green", "已清除；已保存 overlay_keys.json"


def reset() -> tuple[bool, str, str]:
    """恢复默认绑定并清空 warnings。"""
    _STATE["bindings"] = default_bindings()
    _STATE["warnings"] = {}
    save()
    return True, "green", "已恢复默认绑键；已保存 overlay_keys.json"


# ---------------------------------------------------------------- 轮询输出

def vk_map(bindings=None) -> dict:
    """{vk: action_id}；未绑定/非法键跳过。运行时 _poll_hotkeys 用。"""
    store = bindings if bindings is not None else _STATE["bindings"]
    out = {}
    for aid, v in store.items():
        vk = vk_of(v)
        if vk is not None:
            out[vk] = aid
    return out


def pop_warns() -> list:
    """取一次性 warn 列表（读取失败/回退默认提示），取走即清空。"""
    out = list(_STATE["warns"])
    _STATE["warns"].clear()
    return out


def bindings() -> dict:
    return dict(_STATE["bindings"])


def warnings() -> dict:
    return dict(_STATE["warnings"])
