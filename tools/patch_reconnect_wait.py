# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "war_scout_capture.py")
t = open(p, encoding="utf-8").read()
t = t.replace('''    # 断线重连处理
    for _ in range(3):
        img = screencap(cur)
        hit = find(img, "重新载入")
        if hit:
            print("reconnect dialog -> tap", flush=True)
            tap(hit[0], hit[1], 6)
            continue
        break''',
'''    # 断线重连处理（重载需要时间，多等）
    for _ in range(4):
        img = screencap(cur)
        hit = find(img, "重新载入")
        if hit:
            print("reconnect dialog -> tap", flush=True)
            tap(hit[0], hit[1], 20)
            continue
        break''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("reconnect wait patched")
