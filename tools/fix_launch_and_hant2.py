# -*- coding: utf-8 -*-
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
B = chr(96)  # PowerShell 续行反引号

# 1) build: collect zhconv data
p = os.path.join(BASE, "build_overlay.ps1")
t = open(p, encoding="utf-8").read()
target = "    --hidden-import zhconv " + B
if "--collect-data zhconv" not in t:
    t = t.replace(target, target + "\n    --collect-data zhconv " + B, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("build: collect zhconv data")

# 2) exe 无参数启动 -> PANEL 可见
p2 = os.path.join(BASE, "overlay_exe_main.py")
t2 = open(p2, encoding="utf-8").read()
if "bare_launch" not in t2:
    t2 = t2.replace("def main() -> None:\n    from clashlab import __version__\n    ap = argparse.ArgumentParser()",
                    "def main() -> None:\n    from clashlab import __version__\n    bare_launch = len(sys.argv) == 1  # 双击启动（无参数）\n    ap = argparse.ArgumentParser()", 1)
    ins = ("    a = ap.parse_args()\n"
           "    if bare_launch:\n"
           "        # 双击看不到窗口的修复：默认开 PANEL 且可见\n"
           "        if a.show is None:\n"
           "            a.show = True\n"
           "        if a.mode is None:\n"
           "            a.mode = 'PANEL'\n")
    if "    a = ap.parse_args()\n" in t2:
        t2 = t2.replace("    a = ap.parse_args()\n", ins, 1)
        print("entry: bare launch -> PANEL visible")
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
