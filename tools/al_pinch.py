# -*- coding: utf-8 -*-
"""用 sendevent 造双指捏合（协议 B），让游戏镜头缩放。

设备：/dev/input/event2（name "input"），支持 ABS_MT_SLOT / POSITION_X,Y / TRACKING_ID / PRESSURE。
事件码：EV_SYN=0 SYN_REPORT=0；EV_ABS=3；ABS_MT_SLOT=47；ABS_MT_POSITION_X=53；
        ABS_MT_POSITION_Y=54；ABS_MT_TRACKING_ID=57；ABS_MT_PRESSURE=58；EV_KEY=1 BTN_TOUCH=330。
"""
import subprocess, sys, time
ADB = r"E:\leidian\LDPlayer9\adb.exe"
DEV = "emulator-5554"
EV = "/dev/input/event2"


def sh(args, timeout=40):
    return subprocess.run([ADB, "-s", DEV] + args, capture_output=True, timeout=timeout)


def se(typ, code, val):
    return "sendevent %s %d %d %d" % (EV, typ, code, val)


def pinch(cx=640, cy=360, start_gap=60, end_gap=260, steps=12, t=8, hold_ms=0):
    """两指从 (cx±start_gap) 拉到 (cx±end_gap)：>1 放大，<1 缩小。"""
    lines = []
    x0a, x1a = cx - start_gap, cx + start_gap
    x0b, x1b = cx - end_gap, cx + end_gap
    lines += [se(1, 330, 1)]                       # BTN_TOUCH down
    # 两指按下
    lines += [se(3, 47, 0), se(3, 57, 100), se(3, 53, x0a), se(3, 54, cy), se(3, 58, 2)]
    lines += [se(0, 0, 0)]
    lines += [se(3, 47, 1), se(3, 57, 101), se(3, 53, x1a), se(3, 54, cy), se(3, 58, 2)]
    lines += [se(0, 0, 0)]
    # 分步移动
    for i in range(1, steps + 1):
        xa = int(round(x0a + (x0b - x0a) * i / steps))
        xb = int(round(x1a + (x1b - x1a) * i / steps))
        lines += [se(3, 47, 0), se(3, 53, xa), se(3, 54, cy)]
        lines += [se(3, 47, 1), se(3, 53, xb), se(3, 54, cy)]
        lines += [se(0, 0, 0)]
    if hold_ms:
        time.sleep(hold_ms / 1000.0)
    # 抬起
    lines += [se(3, 47, 0), se(3, 57, 4294967295)]
    lines += [se(3, 47, 1), se(3, 57, 4294967295)]
    lines += [se(1, 330, 0), se(0, 0, 0)]
    script = "\n".join(lines)
    r = sh(["shell", script], timeout=60)
    return r.stdout + r.stderr


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "in"
    if mode == "in":
        print(pinch(start_gap=60, end_gap=260, steps=12).decode("utf-8", "ignore")[:300])
    elif mode == "out":
        print(pinch(start_gap=260, end_gap=60, steps=12).decode("utf-8", "ignore")[:300])
    elif mode == "in2":
        print(pinch(start_gap=40, end_gap=320, steps=16).decode("utf-8", "ignore")[:300])
