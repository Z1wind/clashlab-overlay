# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_scout_capture.py")
t = open(p, encoding="utf-8").read()
t = t.replace('''    # 确保在战争地图：找「敌军 / 我军 / 准备日 / 战斗日」
    if not (find(img, "敌军") or find(img, "我军") or find(img, "准备日") or find(img, "战斗日")):
        # 回主城再按左侧战争按钮
        back()
        tap(75, 650, 3)
        img = screencap(cur)''',
'''    # 确保在战争地图：侦察界面/首页 -> 返回地图
    for _ in range(4):
        img = screencap(cur)
        if find(img, "侦察") or find(img, "敌军阵地") or find(img, "战争地图"):
            back(1.5); continue
        if find(img, "敌军") or find(img, "我军") or find(img, "准备日") or find(img, "战斗日"):
            break
        back(1.5)
    else:
        tap(75, 650, 3)
        img = screencap(cur)''')
t = t.replace('''        hits = [(box, t) for (box, t) in ocr(img) if t.strip().startswith("%d." % i)]''',
'''        import re
        hits = []
        for box, txt in ocr(img):
            m = re.match(r"\\s*([0-9Il]{1,2})\\s*[\\.\\,\\s]", txt.strip())
            if not m:
                continue
            num = m.group(1).replace("I", "1").replace("l", "1")
            if num.isdigit() and int(num) == i:
                hits.append((box, txt))''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("pipeline patched")
