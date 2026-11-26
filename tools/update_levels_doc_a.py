# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "docs", "LEVELS.md")
t = open(p, encoding="utf-8").read()
add = '''
## A 方案：TH16 满级回填（2026-11-26 落地）

6 个已标注阵（151 栋）按 reviewed ruleset 的 TH16 最高等级回填 @@@buildings[].level@@@：

@@@
python tools\\apply_max_levels.py --th 16            # 补缺失（默认）
python tools\\apply_max_levels.py --th 16 --overwrite  # 全量覆盖
@@@

关键等级（@@@knowledge/th_ruleset.json@@@ 的 max_levels）：cannon 21 / x-bow 11 / air-defense 14 /
inferno-tower 10 / scattershot 5 / monolith 3 / eagle-artillery 7 / town-hall 16 / clan-castle 12。

回填后实测（@@@out/annotate/03_annotated.json@@@，@@@{giant:10, wizard:12}@@@，20 trials，seed=1）：

| 场景 | 摧毁率 mean | p10 | p90 |
|---|---|---|---|
| 满级阵 | **22.32%** | 13.93% | 32.86% |
| 同一阵所有建筑降到 40% 等级 | **39.82%** | 21.07% | 57.50% |
| 满级阵 + 低配兵/英雄（giant3/wizard3/queen10/king10） | **7.32%** | 0.00% | 14.29% |

备份在 @@@out/annotate/NN_annotated.json.bak_lv@@@；人工修正在标注工具的「等级 Lv」输入框里改即可。

**局限**：这 6 个阵来自布局站，按满级假设回填；若实际对阵玩家有未满级建筑，请在标注工具里改对应那几栋，
推演会自动用新等级。配色自动识别（@@@tools/infer_levels.py@@@）目前不可靠，需等人工等级标签做校准。
'''.replace("@@@", chr(96))
if "A 方案：TH16 满级回填" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("LEVELS.md updated")
else:
    print("already present")
