# -*- coding: utf-8 -*-
"""ADB 通道：取帧、查前台、点击。所有点击默认 dry_run，不会被真正下发。"""
import subprocess
import time
import numpy as np
import cv2


class AdbError(RuntimeError):
    pass


class Adb:
    def __init__(self, adb_path: str, serial: str = "", timeout: float = 15.0):
        if not adb_path:
            raise AdbError("没有找到 adb.exe，请设置环境变量 CLASHLAB_ADB")
        self.adb = adb_path
        self.serial = serial
        self.timeout = timeout

    # ---------- 基础 ----------
    def _run(self, args, binary=False, timeout=None):
        cmd = [self.adb]
        if self.serial:
            cmd += ["-s", self.serial]
        cmd += args
        cp = subprocess.run(cmd, capture_output=True, timeout=timeout or self.timeout)
        if cp.returncode != 0 and not binary:
            raise AdbError(cp.stderr.decode("utf-8", "ignore").strip() or "adb 调用失败")
        return cp.stdout if binary else cp.stdout.decode("utf-8", "ignore")

    def devices(self):
        out = self._run(["devices"])
        rows = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                rows.append(parts[0])
        return rows

    def connect(self, host="127.0.0.1:5555"):
        try:
            self._run(["connect", host])
        except Exception:
            return False
        return True

    def ensure_device(self):
        devs = self.devices()
        if self.serial and self.serial in devs:
            return self.serial
        if devs:
            self.serial = devs[0]
            return self.serial
        for host in ("127.0.0.1:5555", "127.0.0.1:5557", "127.0.0.1:5559"):
            self.connect(host)
        devs = self.devices()
        if not devs:
            raise AdbError("没有可用的 adb 设备，请先启动雷电模拟器")
        self.serial = devs[0]
        return self.serial

    # ---------- 查询 ----------
    def wm_size(self):
        out = self._run(["shell", "wm", "size"])
        for line in out.splitlines():
            if "Override size" in line:
                val = line.split(":")[-1].strip()
            elif "Physical size" in line:
                val = line.split(":")[-1].strip()
            else:
                continue
            try:
                w, h = val.lower().split("x")
                return int(w), int(h)
            except Exception:
                continue
        return (0, 0)

    def current_focus(self):
        try:
            out = self._run(["shell", "dumpsys", "window"])
        except Exception:
            return ""
        for line in out.splitlines():
            if "mCurrentFocus" in line and "Window{" in line:
                return line.split("u0")[-1].strip().rstrip("}")
        return ""

    def packages(self, third_party_only=True):
        args = ["shell", "pm", "list", "packages"]
        if third_party_only:
            args.append("-3")
        out = self._run(args)
        return [l.replace("package:", "").strip() for l in out.splitlines() if l.startswith("package:")]

    def find_coc(self):
        for p in self.packages():
            low = p.lower()
            if "clashofclans" in low or "clash.of.clans" in low:
                return p
        return ""

    # ---------- 取帧 ----------
    def screencap(self):
        t0 = time.perf_counter()
        raw = self._run(["exec-out", "screencap", "-p"], binary=True, timeout=20)
        ms = (time.perf_counter() - t0) * 1000
        if not raw:
            raise AdbError("screencap 返回空数据")
        frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise AdbError("截图解码失败")
        return frame, ms, len(raw)

    # ---------- 输入（默认不下发） ----------
    def tap(self, x, y, dry_run=True):
        if dry_run:
            return False
        self._run(["shell", "input", "tap", str(int(x)), str(int(y))])
        return True

    def swipe(self, x1, y1, x2, y2, dur_ms=300, dry_run=True):
        if dry_run:
            return False
        self._run(["shell", "input", "swipe", str(int(x1)), str(int(y1)),
                   str(int(x2)), str(int(y2)), str(int(dur_ms))])
        return True
