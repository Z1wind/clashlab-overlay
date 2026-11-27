# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_scout_capture.py")
t = open(p, encoding="utf-8").read()
t = t.replace('''    # 确保在战争地图：侦察界面/首页 -> 返回地图
    for _ in range(4):
        img = screencap(cur)
        if find(img, "侦察") or find(img, "敌军阵地") or find(img, "战争地图"):
            back(1.5); continue
        if find(img, "敌军") or find(img, "我军") or find(img, "准备日") or find(img, "战斗日"):
            break
        back(1.5)
    else:
        tap(75, 650, 3)
        img = screencap(cur)''',
'''    # 确保在战争地图（OCR 状态机，不用 back 以免触发退出确认）
    for _ in range(6):
        img = screencap(cur)
        if find(img, "确定退出"):
            hit = find(img, "取消")
            if hit:
                tap(hit[0], hit[1], 1.5)
            continue
        if find(img, "战争地图"):
            hit = find(img, "战争地图")
            tap(hit[0], hit[1], 2.5)
            continue
        if find(img, "敌军") or find(img, "我军") or find(img, "准备日") or find(img, "战斗日"):
            break
        tap(75, 650, 2.5)
    img = screencap(cur)''')
t = t.replace('''        back(2); back(1.5)''', '''        hit = find(img2, "战争地图")
        if hit:
            tap(hit[0], hit[1], 2.5)
        else:
            back(1.5)''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("patched state machine")
