# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_scout_capture.py")
t = open(p, encoding="utf-8").read()
if "重新载入" not in t:
    t = t.replace('''    # 确保在战争地图（OCR 状态机，不用 back 以免触发退出确认）
    for _ in range(6):''',
'''    # 断线重连处理
    for _ in range(3):
        img = screencap(cur)
        hit = find(img, "重新载入")
        if hit:
            print("reconnect dialog -> tap", flush=True)
            tap(hit[0], hit[1], 6)
            continue
        break
    # 确保在战争地图（OCR 状态机，不用 back 以免触发退出确认）
    for _ in range(8):''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("reconnect handling added")
