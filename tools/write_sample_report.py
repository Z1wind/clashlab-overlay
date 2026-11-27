# -*- coding: utf-8 -*-
import json, glob, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
lines = ["# 样例报告：6 套 TH16 阵型的评分 + 穿云箭（2026-11-27）\n",
         "> 数据：out/annotate/01–06_annotated.json（人工标注 76–86 栋/阵），工具：tools/enemy_pipeline.py\n",
         "## 总表\n",
         "| 阵 | 名称 | 评分 | 等级 | 建筑数 | 穿云箭 from → to | 命中 | 对空命中 | 候选线 |",
         "|---|---|---|---|---|---|---|---|---|"]
for d in sorted(glob.glob(os.path.join(BASE, "out", "enemy_report", "0*"))):
    r = json.load(open(os.path.join(d, "report.json"), encoding="utf-8"))
    sc = r.get("score") or {}
    b = r.get("arrow_best") or {}
    hits = b.get("hits") or []
    air = len([h for h in hits if isinstance(h, dict) and h.get("type") in ("air-defense", "air-sweeper")])
    lines.append("| %s | %s | %s | %s | %s | %s → %s | %s | %s | %s |" % (
        os.path.basename(d)[:2], (sc.get("name") or "")[:26], sc.get("overall"), sc.get("grade"),
        r.get("buildings"), b.get("from"), b.get("to"), len(hits), air, len(r.get("arrow_candidates") or [])))
lines += ["",
          "## 评分构成说明（以 01 为例）",
          "- 大本营保护 46.4（中心度 0.77，墙覆盖率按标注折线未计入 → 墙类指标偏低）",
          "- 资源仓保护 29.5（6 个仓库露在边缘）",
          "- 对空覆盖 94.2 / 对地覆盖 95.3（31/40 个防御覆盖）",
          "- 隔间质量 0 / 墙体效率 4.3：**这批标注的墙是连续折线，不是逐格墙体**，墙相关指标仅供参考",
          "- 入口防守 100（4 边都有防守）",
          "",
          "## 怎么看穿云箭结果",
          "- from→to 是 44×44 格坐标（0,0=菱形顶点，x 向右下，y 向左下）",
          "- 命中 = 箭线覆盖的关键防御数；对空命中 = 其中吹风机/防空火箭（穿云箭优先打的目标）",
          "- tesla_warning：特斯拉隐身未探明时给风险提示（本轮 6 阵均无隐藏特斯拉告警）",
          "- placement_sensitivity：英雄落点 ±0.5 格的箭线方向稳定性（之前批量压测结论：仅 26% 落点稳定，实战要谨慎）",
          "",
          "## 每阵俯视示意图",
          "out/enemy_report/<阵>/arrow_diagram.png（灰=普通防御，红=防空，绿=吹风机，黄箭头=穿云箭最优线）"]
open(os.path.join(BASE, "docs", "SAMPLE_REPORT.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("SAMPLE_REPORT.md written")
