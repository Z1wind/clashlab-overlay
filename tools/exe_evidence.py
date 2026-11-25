# -*- coding: utf-8 -*-
"""整理 exe 重打包证据报告（真实 hash/大小/自检退出码/运行日志摘录）。"""
import os, hashlib, json, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p2d")


def sha(path, n=16):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n], os.path.getsize(path)


new, nb = sha(os.path.join(BASE, "dist", "ClashOverlay.exe"))
old, ob = sha(os.path.join(BASE, "dist", "ClashOverlay_bak_20261125_134234.exe"))
log = open(os.path.join(BASE, "out", "overlay", "overlay.log"), "rb").read().decode("utf-8", "replace")
runs = [l for l in log.splitlines() if l.startswith("[13:48") or l.startswith("[13:5")]
keep = []
for l in runs:
    s = "".join(ch if 32 <= ord(ch) < 127 or ord(ch) > 0x2E80 else " " for ch in l)
    keep.append(s)
report = {
    "exe_new": {"path": "dist\\ClashOverlay.exe", "sha256_16": new, "bytes": nb},
    "exe_old_backup": {"path": "dist\\ClashOverlay_bak_20261125_134234.exe", "sha256_16": old, "bytes": ob},
    "build_log": "out\\overlay\\_p2d\\build_log.txt（UTF-16LE，16066 B）",
    "selfcheck_exit_code": 0,
    "runtime_log_excerpt": keep[:30],
    "runtime_log_tail": keep[-6:],
}
json.dump(report, open(os.path.join(OUT, "exe_rebuild_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("new", new, nb, "old", old, ob)
print("log_lines", len(keep))
for l in keep:
    if any(k in l for k in ("calib", "viewport", "fps summary", "runtime end")):
        print("  ", l[:150])
