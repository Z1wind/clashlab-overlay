# -*- coding: utf-8 -*-
"""赛前兵棋推演 CLI：读 layout.json + 军队构成，输出 Monte Carlo JSON。

示例
----
    python tools/wargame_cli.py \
        --layout bases/th16/03/layout.json \
        --army '{"giant":15,"wizard":20,"earthquake":4}' \
        --trials 200 --seed 1 --out out/wargame/03_seed1.json

输出（stdout）为 UTF-8 JSON；--out 用「临时文件 + os.replace」原子落盘。
进度/耗时写 stderr，不污染 stdout 的 JSON。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from clashlab.wargame import (  # noqa: E402
    DEFAULT_MAX_TIME,
    DEFAULT_TICK,
    DEFAULT_TRIALS,
    DEFAULT_WALL_HP,
    run,
)


def _parse_army_arg(text):
    """--army 支持内联 JSON 或 @file.json。"""
    s = str(text).strip()
    if s.startswith("@"):
        path = s[1:]
        with open(path, "r", encoding="utf-8") as f:
            s = f.read()
    try:
        obj = json.loads(s)
    except json.JSONDecodeError as e:
        raise ValueError("--army 不是合法 JSON: %s" % (e,))
    if not isinstance(obj, dict):
        raise ValueError("--army 必须是 JSON 对象，例如 {\"giant\":15}")
    return obj


def _atomic_write_json(path, payload):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def build_parser():
    ap = argparse.ArgumentParser(
        prog="wargame_cli",
        description="赛前兵棋推演：确定性 tick + Monte Carlo，输出摧毁率分布与最佳投放点 JSON。")
    ap.add_argument("--layout", required=True,
                    help="layout.json 路径，例如 bases/th16/03/layout.json")
    ap.add_argument("--army", required=True,
                    help='军队构成 JSON，例如 \'{"giant":15,"wizard":20,"earthquake":4}\'，也支持 @file.json')
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS,
                    help="Monte Carlo 次数（默认 %d）" % DEFAULT_TRIALS)
    ap.add_argument("--seed", type=int, default=1, help="随机种子（默认 1）")
    ap.add_argument("--out", default=None, help="把结果 JSON 写入该路径（原子写）")
    ap.add_argument("--tick", type=float, default=DEFAULT_TICK,
                    help="推演步长秒（默认 %s）" % DEFAULT_TICK)
    ap.add_argument("--max-time", type=float, default=DEFAULT_MAX_TIME,
                    help="单场最长游戏秒（默认 %s）" % DEFAULT_MAX_TIME)
    ap.add_argument("--wall-hp", type=float, default=DEFAULT_WALL_HP,
                    help="单格墙血量（默认 %s）" % DEFAULT_WALL_HP)
    ap.add_argument("--workers", type=int, default=0,
                    help="并行进程数；0=自动（trials>=64 时用 8 进程，否则串行）")
    ap.add_argument("--quiet", action="store_true", help="不把 JSON 打到 stdout（配合 --out）")
    return ap


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    if args.trials < 1:
        print("[wargame] --trials 必须 >= 1", file=sys.stderr)
        return 2
    try:
        army = _parse_army_arg(args.army)
        t0 = time.perf_counter()
        result = run(args.layout, army, trials=args.trials, seed=args.seed,
                     tick=args.tick, max_time=args.max_time, wall_hp=args.wall_hp,
                     workers=args.workers)
        elapsed = time.perf_counter() - t0
    except (ValueError, OSError, TypeError) as e:
        print("[wargame] 失败: %s" % (e,), file=sys.stderr)
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        try:
            _atomic_write_json(args.out, result)
        except OSError as e:
            print("[wargame] 写 %s 失败: %s" % (args.out, e), file=sys.stderr)
            return 2
    if not args.quiet:
        sys.stdout.write(text + "\n")
    print("[wargame] trials=%d seed=%d elapsed=%.3fs best=%s@%.1f%% layout=%s"
          % (args.trials, args.seed, elapsed, result["best"]["spawn"],
             result["best"]["destruction"], args.layout), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
