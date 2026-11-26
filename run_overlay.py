# -*- coding: utf-8 -*-
"""覆盖层入口：python run_overlay.py [--show] [--seconds N] [--root DIR]。

默认 show=false（不可见自检，touch_report.md 出现前的协作时序）；
--show 进入可见 HUD/PANEL。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clashlab.overlay.runtime import run


def main():
    from clashlab import __version__
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", action="version", version="ClashLab " + __version__)
    ap.add_argument("--root", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--show", action="store_true", help="可见覆盖层（默认不可见自检）")
    ap.add_argument("--seconds", type=float, default=None, help="自检模式退出秒数")
    ap.add_argument("--run-seconds", type=float, default=None, help="可见模式运行秒数后退出")
    ap.add_argument("--mode", default=None, choices=["HUD", "PANEL"], help="启动模式")
    ap.add_argument("--always-on-top", action="store_true",
                    help="常显（默认关闭=跟随前台，雷电不在前台即隐藏）")
    ap.add_argument("--lang", default=None, choices=["auto", "zh", "zh-hant", "en"],
                    help="UI language: auto / zh / en (overrides config/ui.json)")
    ap.add_argument("--allow-primary", action="store_true",
                    help="逃生开关（不建议使用）：允许覆盖层出现在主显示器；"
                         "默认关闭=渲染窗口在主屏即强制隐藏")
    a = ap.parse_args()
    if getattr(a, "lang", None):
        os.environ["CLASHLAB_LANG"] = a.lang

    cfg = {}
    if a.show:
        cfg["show"] = True
    if a.seconds:
        cfg["self_check_seconds"] = a.seconds
    if a.run_seconds:
        cfg["run_seconds"] = a.run_seconds
    if a.mode:
        cfg["mode"] = a.mode
    if a.always_on_top:
        cfg["always_on_top"] = True
    if a.allow_primary:
        cfg["allow_primary"] = True
    run(a.root, cfg)


if __name__ == "__main__":
    main()
