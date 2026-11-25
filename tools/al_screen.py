# -*- coding: utf-8 -*-
import subprocess, sys, os
ADB = r"E:\leidian\LDPlayer9\adb.exe"
def shot(path):
    out = subprocess.run([ADB, "-s", "emulator-5554", "exec-out", "screencap", "-p"], capture_output=True)
    data = out.stdout
    with open(path, "wb") as f:
        f.write(data)
    return len(data), data[:8]
if __name__ == "__main__":
    p = sys.argv[1]
    n, head = shot(p)
    print("bytes", n, "head", head)