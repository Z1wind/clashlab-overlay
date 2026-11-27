# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "layout_rules.py")
t = open(p, encoding="utf-8").read()
t = t.replace('''def _rule(rid, title, severity, passed, evidence, rec):
    return {"id": rid, "title": title, "severity": severity, "passed": bool(passed),
            "evidence": evidence, "recommendation": None if passed else rec}''',
'''def _rule(rid, title, severity, passed, evidence, rec, skipped=False):
    return {"id": rid, "title": title, "severity": severity, "passed": bool(passed),
            "skipped": bool(skipped), "evidence": evidence,
            "recommendation": None if (passed or skipped) else rec}''')
# wall confidence + skip wall rules
t = t.replace('''    # R1 大本是否被墙围
    rules.append(_rule("R1", "大本被墙保护", "critical", grid.th_inside_walls(),
                       "闭合隔间内的主堡" if grid.th_inside_walls() else "大本不在任何闭合墙体内",
                       "给大本围一圈闭合墙，至少覆盖 3 面"))''',
'''    comps = grid.compartments(min_tiles=4)
    wall_conf = "high" if len(comps) >= 1 else "low"  # 墙数据不闭合时，墙类规则只提示不判负
    # R1 大本是否被墙围
    _th_ok = grid.th_inside_walls()
    rules.append(_rule("R1", "大本被墙保护", "critical", _th_ok,
                       ("闭合隔间内的主堡" if _th_ok else "大本不在任何闭合墙体内")
                       if wall_conf == "high" else "墙数据不完整（无闭合隔间），该规则未判定",
                       "给大本围一圈闭合墙，至少覆盖 3 面", skipped=(wall_conf != "high")))''')
t = t.replace('''    # R5 隔间数量（墙结构质量）
    comps = grid.compartments(min_tiles=4)
    rules.append(_rule("R5", "墙隔间 ≥4", "warn", len(comps) >= 4, "闭合隔间 %d 个" % len(comps),
                       "用墙分出更多隔间（≥4），拖慢地面部队"))''',
'''    # R5 隔间数量（墙结构质量）
    rules.append(_rule("R5", "墙隔间 ≥4", "warn", len(comps) >= 4,
                       "闭合隔间 %d 个" % len(comps),
                       "用墙分出更多隔间（≥4），拖慢地面部队", skipped=(wall_conf != "high")))''')
t = t.replace('''    iso = grid.wall_efficiency()
    rules.append(_rule("R6", "墙体连贯", "warn", iso <= 0.25, "孤立墙比例 %.0f%%" % (iso * 100),
                       "把断墙连成闭合圈（孤立墙 %.0f%%）" % (iso * 100)))''',
'''    iso = grid.wall_efficiency()
    rules.append(_rule("R6", "墙体连贯", "warn", iso <= 0.25, "孤立墙比例 %.0f%%" % (iso * 100),
                       "把断墙连成闭合圈（孤立墙 %.0f%%）" % (iso * 100), skipped=(wall_conf != "high")))''')
t = t.replace('''    weight = {"critical": 3, "warn": 2, "info": 1}
    total = sum(weight[r["severity"]] for r in rules)
    got = sum(weight[r["severity"]] for r in rules if r["passed"])''',
'''    weight = {"critical": 3, "warn": 2, "info": 1}
    scored = [r for r in rules if not r.get("skipped")]
    total = sum(weight[r["severity"]] for r in scored)
    got = sum(weight[r["severity"]] for r in scored if r["passed"])''')
t = t.replace('''    return {"score": score, "grade": grade, "rules": rules,
            "failed": [r for r in rules if not r["passed"]],''',
'''    return {"score": score, "grade": grade, "rules": rules, "wall_confidence": wall_conf,
            "skipped": [r["id"] for r in rules if r.get("skipped")],
            "failed": [r for r in rules if (not r["passed"] and not r.get("skipped"))],''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("rules skip-wall patch done")

# 更新测试预期：无墙时不判 critical 失败，改为断言 R3 失败 + R1/R5 跳过
p2 = os.path.join(BASE, "tests", "test_layout_rules.py")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace('''        ids = [x["id"] for x in r["failed"]]
        self.assertIn("R1", ids)
        self.assertIn("R3", ids)''',
'''        ids = [x["id"] for x in r["failed"]]
        self.assertIn("R3", ids)               # 防空规则仍然判失败
        self.assertIn("R1", r["skipped"])      # 墙数据不完整 -> R1 不判定''')
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("tests updated")
