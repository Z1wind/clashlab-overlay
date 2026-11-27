# -*- coding: utf-8 -*-
import os, zipfile, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
out = os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127.zip")
os.makedirs(os.path.dirname(out), exist_ok=True)
if os.path.exists(out):
    os.remove(out)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for i in ("01", "02", "03", "04", "05", "06"):
        d = os.path.join(BASE, "out", "enemy_report", i + "_annotated")
        for fn in ("report.json", "arrow_diagram.png"):
            p = os.path.join(d, fn)
            if os.path.exists(p):
                z.write(p, i + "_annotated/" + fn)
    for extra in ("docs/SAMPLE_REPORT.md", "docs/STATUS.md"):
        p = os.path.join(BASE, extra)
        if os.path.exists(p):
            z.write(p, os.path.basename(extra))
print("zip", out, os.path.getsize(out))

doc = ("# ClashLab v0.3.1（2026-11-27）\n\n"
       "## 新增\n"
       "- tools/report_one.py：一条命令从 annotated JSON 出「评分报告 + 俯视箭线图 + Markdown 摘要」\n"
       "- docs/SAMPLE_REPORT.md：6 套 TH16 阵样例报告（评分 52.4–63.7，每阵 3 条箭线候选）\n\n"
       "## 修复 / 变更\n"
       "- PANEL 点击不切换（去双鼠标通道）、研究/设置页重叠、调试锚点默认隐藏、单实例互斥\n"
       "- 手机标注 APK v2（内置 3 张真实战图；4 角标定 + 建筑点选 + JSON 导出）\n"
       "- 训练数据排除 firespitter（用户误标）\n\n"
       "## 研究结论（失败并停止）\n"
       "- C 检测器：纯合成数据训练在真实战图 30 框全错 → docs/C_DETECT_SPIKE.md\n"
       "- 自动标注：6 种标定法 + quad_model + 滑窗分类器均不可用 → docs/AUTO_ANNOTATE_FAIL.md\n\n"
       "> 非官方工具；请自行评估 ToS 风险。\n")
open(os.path.join(BASE, "docs", "RELEASE_v0.3.1.md"), "w", encoding="utf-8", newline="\n").write(doc)
print("release notes written")
