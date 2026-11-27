# -*- coding: utf-8 -*-
"""ClashOverlay.exe packaging shim (not business logic).

Frozen (PyInstaller onefile):
  * data root = directory of the exe (relative resolution, no absolute hardcode);
  * CLASHLAB_ROOT env also set for the panel data layer;
  * visible by default (double-click shows HUD); --no-show forces self-check.
Source:
  * behaves like run_overlay.py; project root = this file's directory.

Business entry remains run_overlay.py; this shim only resolves root and flags.
"""
import argparse
import os
import sys


def _looks_like_root(path: str) -> bool:
    r"""真实数据根标记：光有 out\ 不算（EXE 自己会建日志目录）。"""
    markers = (
        os.path.join("config", "anchors.json"),
        os.path.join("out", "prebattle"),
        os.path.join("out", "snap"),
        os.path.join("clashlab", "geo.py"),
    )
    return any(os.path.exists(os.path.join(path, m)) for m in markers)


def _default_root() -> str:
    """数据根两级兜底（P0-1）：exe 同目录 → %LOCALAPPDATA%\\ClashOverlay。
    严禁回退到用户主目录（C:\\Users）——那会把 out/ 写到家里、跑偏。
    两级都无锚点时仍返回 exe 同目录，由界面层出中文缺数据提示。"""
    if getattr(sys, "frozen", False):
        d = os.path.dirname(os.path.abspath(sys.executable))
        probe = d
        for _ in range(3):
            if _looks_like_root(probe):
                break
            parent = os.path.dirname(probe)
            if parent == probe:
                probe = d
                break
            probe = parent
        if not _looks_like_root(probe):
            lad = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ClashOverlay")
            if lad and os.path.isdir(lad) and _looks_like_root(lad):
                probe = lad
            else:
                probe = d  # exe 同目录兜底（无锚点 -> 界面中文提示）
        os.environ.setdefault("CLASHLAB_ROOT", probe)
        return probe
    return os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    from clashlab import __version__
    bare_launch = len(sys.argv) == 1  # 双击启动（无参数）
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", action="version", version="ClashLab " + __version__)
    ap.add_argument("--root", default=_default_root())
    ap.add_argument("--show", dest="show", action="store_true", default=None)
    ap.add_argument("--no-show", dest="show", action="store_false")
    ap.add_argument("--seconds", type=float, default=None,
                    help="self-check exit seconds (self-check mode)")
    ap.add_argument("--run-seconds", type=float, default=None,
                    help="visible mode auto-exit seconds")
    ap.add_argument("--mode", default=None, choices=["HUD", "PANEL"],
                    help="start mode")
    ap.add_argument("--always-on-top", action="store_true",
                    help="always visible (default: follow foreground, hide when LDPlayer not front)")
    ap.add_argument("--lang", default=None, choices=["auto", "zh", "zh-hant", "en"],
                    help="UI language: auto / zh / en")
    ap.add_argument("--allow-primary", action="store_true",
                    help="allow target on primary display (single-monitor setups)")
    ap.add_argument("--ocr-selftest", nargs=2, metavar=("IMAGE", "OUT_JSON"), default=None,
                    help="offline OCR self-test: read image -> write parsed result JSON")
    a = ap.parse_args()
    if bare_launch:
        # 双击看不到窗口的修复：默认开 PANEL 且可见
        if a.show is None:
            a.show = True
        if a.mode is None:
            a.mode = 'PANEL'
        if not a.allow_primary:
            a.allow_primary = True  # 双击在单屏/主屏也可见（否则被主屏守卫隐藏）
    if getattr(a, "lang", None):
        import os as _os
        _os.environ["CLASHLAB_LANG"] = a.lang

    if a.ocr_selftest:
        import json
        import numpy as np
        import cv2
        from clashlab import ocr_screen
        img = cv2.imdecode(np.fromfile(a.ocr_selftest[0], np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise SystemExit("read image failed: " + a.ocr_selftest[0])
        got = ocr_screen.read_opponent(img)
        with open(a.ocr_selftest[1], "w", encoding="utf-8") as f:
            json.dump(got, f, ensure_ascii=False, indent=1)
        return

    from clashlab.overlay.runtime import run

    cfg: dict = {}
    if a.show is not None:
        cfg["show"] = bool(a.show)
    elif getattr(sys, "frozen", False):
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
