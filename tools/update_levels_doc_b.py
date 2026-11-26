# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "docs", "LEVELS.md")
t = open(p, encoding="utf-8").read()
add = '''
## 标注更新（2026-11-26 13:40，用户补标后）

- 6 个标注阵合计 **262 栋**（01: 86、02: 82、03: 28、04: 24、05: 24、06: 18）；用户补进了经济/兵营等建筑。
- 等级回填后 **0 栋缺 level**（规则：reviewed ruleset 的 TH16 最高等级；查不到的类型跳过）。
- 顺手修了一个推演偏差：**经济/兵营/陷阱等非防御建筑以前会走 DEFAULT_FALLBACK（dps=120），被当成防御**；
  现在只有 @@@assets.STATS@@@ / @@@TH16_OVERRIDE@@@ 里的类型算防御，其它建筑 dps=0、尺寸查 ruleset。
  影响：01 阵（86 栋）同样军队的摧毁率从 **9.88% → 10.93%**（少了 9 个「假防御」）。
- 单测：新增 @@@tests/test_wargame_economy.py@@@ 3 项（经济建筑 dps=0、尺寸来自 ruleset、推演可跑）。
'''.replace("@@@", chr(96))
if "标注更新（2026-11-26" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("LEVELS.md updated")
