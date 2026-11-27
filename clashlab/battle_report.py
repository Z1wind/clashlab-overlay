# -*- coding: utf-8 -*-
"""一键战报：规则评分 + 修复建议 + 穿云箭 + 战斗模拟 + 推荐打法，输出自包含 HTML。"""
from __future__ import annotations
import base64, html, json, os, time

BASE = os.environ.get("CLASHLAB_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAR_MAP = {"critical": "#e0533d", "warn": "#e0a13c", "info": "#4a8bd6", "ok": "#58b368"}


def _icon_b64(uid):
    d = os.path.join(BASE, "assets", "units_real")
    for ext in (".webp", ".png"):
        p = os.path.join(d, uid + ext)
        if os.path.exists(p):
            try:
                if ext == ".webp":
                    import cv2, numpy as np
                    img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)
                    if img is None:
                        continue
                    ok, buf = cv2.imencode(".png", img)
                    if not ok:
                        continue
                    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode("ascii")
                return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode("ascii")
            except Exception:
                continue
    return ""


def build(layout_path=None, out_path=None, th=None, army=None, open_after=False, layout=None):
    from . import layout_rules, battle_sim, units, strategy
    try:
        import giant_arrow_diagram as ga  # 兼容旧路径
    except Exception:
        ga = None
    if layout is None:
        layout = json.load(open(layout_path, encoding="utf-8"))
    name = layout.get("name") or (os.path.splitext(os.path.basename(layout_path))[0] if layout_path else "current")
    rules = layout_rules.evaluate(layout)
    army = army or {"miner": 21, "hog-rider": 11, "healer": 4}
    spells = {"heal": 3, "rage": 2}
    heroes = ["queen", "king"]
    sim = battle_sim.simulate(layout, army, spells=spells, th=th, heroes=heroes)
    try:
        recs = strategy.recommend(None, th=th, limit=5)
        if isinstance(recs, dict):
            recs = recs.get("recommendations") or recs.get("items") or []
    except Exception:
        recs = []
    arrow = None
    if ga is not None:
        try:
            lines = ga.candidate_arrow_lines(layout)
            best = ga.optimize_giant_arrow(layout, lines) if lines else None
            if best:
                hits = ga.summarize_hits(layout, best["frm"], best["to"])
                arrow = {"line": [best["frm"], best["to"]], "score": ga.score_hits(hits), "hits": hits}
        except Exception:
            arrow = None

    def row(k, v):
        return "<tr><th>%s</th><td>%s</td></tr>" % (html.escape(str(k)), html.escape(str(v)))

    rule_rows = []
    for r in rules.get("rules") or []:
        st = r.get("status")
        color = BAR_MAP.get("critical" if st == "fail" and r.get("severity") == "critical" else
                            "warn" if st == "fail" else "ok", "#9fb3c8")
        rule_rows.append('<tr><td><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:%s"></span> %s</td>'
                         '<td>%s</td><td style="color:#9fb3c8">%s</td></tr>' % (
                             color, html.escape(r.get("id", "")), html.escape(r.get("title", "")),
                             html.escape(str(r.get("detail") or r.get("evidence") or ""))[:160]))

    sim_rows = []
    if sim.get("ok"):
        sim_rows = [row("推荐进攻侧", sim["side"]), row("路径长度", "%s 格（破墙 %s）" % (sim["path_len"], sim["walls_to_break"])),
                    row("暴露 DPS", sim["exposure_dps"]), row("生存率", "%.0f%%" % (sim["survival"] * 100)),
                    row("拆本时间", "%ss" % sim["th_ttk_s"]), row("预估星级", "%d ★" % sim["stars_estimate"])]
    army_chips = []
    for tid, cnt in army.items():
        u = units.TROOPS.get(tid) or {}
        icon = _icon_b64(tid)
        img = ('<img src="%s" style="width:30px;height:30px;border-radius:7px;vertical-align:middle">' % icon) if icon else ""
        army_chips.append('<span class="chip">%s %s×%s</span>' % (img, html.escape(u.get("zh", tid)), cnt))
    spell_chips = []
    for sid, cnt in spells.items():
        s = units.SPELLS.get(sid) or {}
        icon = _icon_b64(sid)
        img = ('<img src="%s" style="width:30px;height:30px;border-radius:7px;vertical-align:middle">' % icon) if icon else ""
        spell_chips.append('<span class="chip sp">%s %s×%s</span>' % (img, html.escape(s.get("zh", sid)), cnt))
    rec_html = ""
    for r in (recs or [])[:5]:
        rec_html += '<div class="rec"><b>%s</b> <span style="color:#9fb3c8">%s</span><br>%s</div>' % (
            html.escape(str(r.get("name") or r.get("id") or "")), html.escape(str(r.get("source") or "")),
            html.escape(str(r.get("steps") or r.get("summary") or ""))[:220])
    arrow_html = ""
    if arrow:
        arrow_html = '<div class="rec"><b>穿云箭最优落点</b>：%s → %s，评分 %.1f，命中 %s</div>' % (
            html.escape(str(arrow["line"][0])), html.escape(str(arrow["line"][1])), arrow["score"],
            html.escape(str([h.get("type") for h in arrow["hits"]][:8])))

    html_doc = """<!doctype html><html><head><meta charset="utf-8"><title>战报 - __NAME__</title>
<style>
body{margin:0;background:#0f1318;color:#dde3ea;font-family:system-ui,'Microsoft YaHei',sans-serif;padding:20px}
h1{color:#f0b84a;font-size:22px;margin:0 0 4px}
.sub{color:#8fa3bd;font-size:12px;margin-bottom:16px}
h2{font-size:15px;margin:22px 0 8px;color:#9fd0ff;border-left:4px solid #4a8bd6;padding-left:8px}
.score{font-size:34px;font-weight:700;color:#58b368}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:#9fb3c8;font-weight:500;width:130px;padding:4px 6px;border-bottom:1px solid #222b36}
td{padding:4px 6px;border-bottom:1px solid #222b36}
.chip{display:inline-flex;align-items:center;gap:6px;background:#222b36;border-radius:16px;padding:3px 10px 3px 4px;margin:3px 5px;font-size:13px}
.chip.sp{background:#2a2336}
.rec{background:#151c24;border-radius:8px;padding:8px 10px;margin:6px 0;font-size:12px;line-height:1.7}
.note{color:#7f93ad;font-size:11px;margin-top:18px}
</style></head><body>
<h1>战报：__NAME__</h1>
<div class="sub">等级 __GRADE__（分数 __SCORE__）· 生成于 __TIME__ · ClashLab</div>
<h2>评分与规则</h2>
<div class="score">__SCORE__</div>
<table>__RULES__</table>
<h2>进攻模拟（启发式）</h2>
<table>__SIM__</table>
__ARROW__
<h2>推荐配比</h2>
<div>__ARMY__</div>
<div>__SPELLS__</div>
<h2>推荐打法</h2>
__RECS__
<div class="note">启发式分析，非游戏真实引擎；仅供战术参考。</div>
</body></html>"""
    repl = {
        "__NAME__": html.escape(name), "__GRADE__": html.escape(str(rules.get("grade", ""))),
        "__SCORE__": html.escape(str(rules.get("score", ""))), "__TIME__": time.strftime("%Y-%m-%d %H:%M"),
        "__RULES__": "".join(rule_rows), "__SIM__": "".join(sim_rows), "__ARMY__": "".join(army_chips),
        "__SPELLS__": "".join(spell_chips), "__RECS__": rec_html, "__ARROW__": arrow_html,
    }
    for k, v in repl.items():
        html_doc = html_doc.replace(k, v)
    out_path = out_path or os.path.join(BASE, "out", "reports", (name or "report") + "_battle.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8", newline="\n").write(html_doc)
    if open_after:
        try:
            os.startfile(out_path)
        except Exception:
            pass
    return {"ok": True, "path": out_path, "bytes": os.path.getsize(out_path),
            "score": rules.get("score"), "grade": rules.get("grade"),
            "sim_ok": bool(sim.get("ok")), "stars": sim.get("stars_estimate")}
