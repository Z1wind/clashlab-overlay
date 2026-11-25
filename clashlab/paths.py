# -*- coding: utf-8 -*-
"""项目根锚定路径解析（P0-04）。

问题：双击 exe / 从任意 CWD 启动时，``layouts/...`` 这类相对路径按 CWD 解析，
冻结态找不到阵型与资源。本模块把资源解析锚到「项目根」，不再依赖 CWD，
也不在代码里硬编码任何绝对路径。

探测顺序（命中即停）：
1. 环境变量 ``CLASHLAB_ROOT``（显式覆盖，最高优先）；
2. frozen 态：``sys._MEIPASS``（PyInstaller 解压目录）→ exe 同级目录；
3. 从本文件位置逐级向上探测锚点：``config/anchors.json``、
   ``out/prebattle/info.json``、``out/snap``、``clashlab/geo.py`` 任一存在即认定根；
4. 全部失败再退回 CWD（最后兜底，让调用方按「文件不存在」显式报错）。
"""
import os
import sys

# 任一锚点存在即认定为项目根（相对项目根的路径）
ANCHORS = (
    os.path.join("config", "anchors.json"),
    os.path.join("out", "prebattle", "info.json"),
    os.path.join("out", "snap"),
    os.path.join("clashlab", "geo.py"),
)


def _anchor_hits(base):
    return [a for a in ANCHORS if os.path.exists(os.path.join(base, a))]


def _candidate_roots():
    """按优先级给出待探测目录（不去重、不判存在，交给 project_root 过滤）。"""
    cands = []
    env = os.environ.get("CLASHLAB_ROOT")
    if env:
        cands.append(env)
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            cands.append(meipass)
        cands.append(os.path.dirname(os.path.abspath(sys.executable)))
    # 源码运行：从本文件（clashlab/paths.py）逐级向上
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    while True:
        cands.append(d)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return cands


def project_root():
    """返回项目根绝对路径；锚点全部未命中时退回 CWD（不为空串）。"""
    for base in _candidate_roots():
        if base and os.path.isdir(base) and _anchor_hits(base):
            return os.path.abspath(base)
    return os.path.abspath(os.getcwd())


def resource_base():
    """只读资源基准目录：frozen 走 _MEIPASS，否则项目根。"""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return meipass
    return project_root()


def resolve_resource(rel_or_abs, root=None):
    """把相对资源锚到项目根；绝对路径且存在则原样返回。

    返回解析后的绝对路径（不保证存在，存在性由调用方报错展示）。
    """
    p = rel_or_abs or ""
    if os.path.isabs(p):
        return os.path.abspath(p)
    base = root or project_root()
    joined = os.path.join(base, p)
    if os.path.exists(joined):
        return os.path.abspath(joined)
    # 锚定失败的最后兜底：CWD 相对（仅在此分支，区别于 P0-04 禁止的默认 CWD 裸解析）
    return os.path.abspath(p)


def resolve_layout(path):
    """阵型 JSON 专用解析：相对路径锚项目根，找不到时给出明确提示路径。"""
    resolved = resolve_resource(path)
    if os.path.exists(resolved):
        return resolved, None
    return resolved, f"阵型文件不存在：{resolved}（已锚定项目根 {project_root()}）"
