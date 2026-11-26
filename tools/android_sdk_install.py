# -*- coding: utf-8 -*-
"""安装 Android SDK 组件到 E:\tools\android-sdk（不占 C 盘）。"""
import os, subprocess, sys

SDK = r"E:\tools\android-sdk"
SM = os.path.join(SDK, "cmdline-tools", "latest", "bin", "sdkmanager.bat")
env = dict(os.environ)
env["JAVA_HOME"] = r"E:\tools\jdk17"
env["PATH"] = env["JAVA_HOME"] + r"\bin;" + env.get("PATH", "")

def run(args, feed=None):
    print("$ sdkmanager", " ".join(args), flush=True)
    p = subprocess.run([SM] + args, input=feed, text=True, capture_output=True, env=env)
    out = (p.stdout or "")[-3000:]
    err = (p.stderr or "")[-1500:]
    print(out)
    if err.strip():
        print("STDERR:", err)
    print("exit:", p.returncode, flush=True)
    return p.returncode

if not os.path.exists(SM):
    raise SystemExit("sdkmanager missing: " + SM)
run(["--sdk_root=" + SDK, "--licenses"], feed=("y\n" * 40))
run(["--sdk_root=" + SDK, "platform-tools", "platforms;android-34", "build-tools;34.0.0"])
run(["--sdk_root=" + SDK, "--list_installed"])
print("SDK_INSTALL_DONE")
