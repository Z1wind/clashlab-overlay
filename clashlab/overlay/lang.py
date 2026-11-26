# -*- coding: utf-8 -*-
"""UI 语言（中文 / English）开关：config/ui.json 的 lang 字段 + 环境变量覆盖。

优先级：环境变量 CLASHLAB_LANG（zh/en/auto） > config/ui.json lang > auto。
auto = 沿用旧逻辑：CJK 字体可用则中文，否则英文。
"""
from __future__ import annotations

import json
import os

_MODES = ("auto", "zh", "en")
_current = "auto"
_loaded_root = None


def config_path(root):
    return os.path.join(root, "config", "ui.json")


def _read_config(root):
    try:
        with open(config_path(root), "r", encoding="utf-8") as f:
            doc = json.load(f)
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def ensure_loaded(root):
    """从环境变量/config 初始化一次；root 变化时重读。"""
    global _current, _loaded_root
    if _loaded_root == root:
        return _current
    _loaded_root = root
    env = (os.environ.get("CLASHLAB_LANG") or "").strip().lower()
    if env in _MODES:
        _current = env
        return _current
    val = str(_read_config(root).get("lang") or "auto").strip().lower()
    _current = val if val in _MODES else "auto"
    return _current


def get():
    return _current


def set(root, mode):
    """切换语言并写回 config/ui.json（保留其它字段）。"""
    global _current, _loaded_root
    mode = str(mode or "auto").strip().lower()
    if mode not in _MODES:
        raise ValueError("lang must be one of %s" % (_MODES,))
    _current = mode
    _loaded_root = root
    doc = _read_config(root)
    doc["lang"] = mode
    path = config_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return mode


def label(zh, en):
    """按当前语言取文案；auto 时给中文（字体不可用的情况由 pages 的 ready 逻辑兜底）。"""
    if _current == "en":
        return en
    return zh
