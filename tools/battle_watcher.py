# -*- coding: utf-8 -*-
"""看守：等到战斗日时间后自动抓图 + 出拼图（后台任务用）。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
target = time.mktime(time.strptime("2026-11-27 21:52:00", "%Y-%m-%d %H:%M:%S"))
while time.time() < target:
    time.sleep(20)
print("watcher: battle time reached", time.strftime("%H:%M:%S"), flush=True)
def run(cmd, log):
    with open(os.path.join(BASE, "out", "logs", log), "a", encoding="utf-8") as f:
        f.write("\n=== %s %s ===\n" % (time.strftime("%H:%M:%S"), " ".join(cmd)))
        f.flush()
        p = subprocess.run(cmd, cwd=BASE, stdout=f, stderr=subprocess.STDOUT, timeout=1800)
        return p.returncode
rc1 = run([sys.executable, "-u", "tools\\war_scout_capture.py", "--max", "12"], "watcher_capture.log")
print("capture rc", rc1, flush=True)
rc2 = run([sys.executable, "-u", "tools\\war_base_montage.py", "--glob", "out/live/war1080/base_*.png", "--thr", "0.40"], "watcher_montage.log")
print("montage rc", rc2, flush=True)
print("WATCHER DONE", flush=True)
