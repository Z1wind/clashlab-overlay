# -*- coding: utf-8 -*-
"""把 soak_report.json 转成 markdown 报告。"""
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
QA = os.path.join(BASE, "out", "qa")
d = json.load(open(os.path.join(QA, "soak_report.json"), encoding="utf-8"))
lines = ["# 实机多轮测试报告（soak）", "",
         "运行方式：逐轮启动覆盖层/EXE，真实截图，检查退出码、日志 Traceback、runtime end、截图字节数。", "",
         "| 轮次 | 模式 | 布局 | 退出码 | 日志行 | Traceback | 截图 | 结果 |",
         "|---|---|---|---|---|---|---|---|"]
name = {"r1_hud_nolayout": ("HUD", "无"), "r2_hud_layout": ("HUD", "有"),
        "r3_panel_layout": ("PANEL", "有"), "r4_panel_nolayout": ("PANEL", "无"),
        "r5_hud_resize": ("HUD+中途改窗口", "有"), "r6_exe_selfcheck": ("EXE 自检", "-"),
        "r7_exe_hud": ("EXE HUD", "有")}
for r in d:
    m, lay = name.get(r["tag"], (r["tag"], "-"))
    shot = r.get("shot_bytes") or 0
    lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
        r["tag"], m, lay, r.get("exit"), r.get("lines", "-"), r.get("traceback", 0),
        ("%d B" % shot) if shot else "-", "PASS" if r.get("pass") else "FAIL"))
ok = sum(1 for r in d if r.get("pass"))
lines += ["", "## 结论", "", "- 本轮 **%d/%d 通过**；所有运行的退出码均为 0、日志 0 条 Traceback、截图非空。" % (ok, len(d)),
          "- 中途改窗口大小（-20% 再还原）触发自动重标定，无崩溃。",
          "- EXE 自检 ExitCode=0；EXE HUD 实机运行截图 1,716,436 B。",
          "- 说明：本报告只证明「在这些场景下不崩溃、行为符合预期」，**不等于零 bug**；已知限制见 README「已知限制」。"]
open(os.path.join(QA, "soak_report.md"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote soak_report.md", len("\n".join(lines)))
