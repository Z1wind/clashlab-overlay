# -*- coding: utf-8 -*-
"""P2 前置：三连测 LDPlayerMainFrame / RenderWindow / subWin 矩形（1s 间隔），只读。"""
import ctypes, time, json
import win32gui, win32con

def snap():
    main=[None]
    def _cb(h,_):
        if win32gui.GetClassName(h)=="LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
            main[0]=h
    win32gui.EnumWindows(_cb,None)
    out={"main":None,"children":[]}
    if not main[0]:
        return out
    h=main[0]
    wr=win32gui.GetWindowRect(h)
    cr=win32gui.GetClientRect(h)
    pt=win32gui.ClientToScreen(h,(0,0))
    out["main"]={"rect":list(wr),"client_origin":list(pt),"client_size":[cr[2],cr[3]],
                 "exstyle":hex(win32gui.GetWindowLong(h,win32con.GWL_EXSTYLE))}
    kids=[]
    win32gui.EnumChildWindows(h,lambda k,_:kids.append(k),None)
    seen=set()
    def walk(k):
        if k in seen: return
        seen.add(k)
        if win32gui.IsWindowVisible(k):
            r=win32gui.GetClientRect(k); p=win32gui.ClientToScreen(k,(0,0))
            out["children"].append({"hwnd":int(k),"cls":win32gui.GetClassName(k),
                "client_origin":list(p),"client_size":[r[2],r[3]],
                "win_rect":list(win32gui.GetWindowRect(k)),
                "exstyle":hex(win32gui.GetWindowLong(k,win32con.GWL_EXSTYLE)),
                "area":r[2]*r[3]})
        for k2 in []: pass
    # 递归收集所有后代
    allc=[]
    def collect(k):
        sub=[]
        win32gui.EnumChildWindows(k,lambda x,_:sub.append(x),None)
        for x in sub:
            allc.append(x); collect(x)
    collect(h)
    for k in allc:
        if win32gui.IsWindowVisible(k):
            r=win32gui.GetClientRect(k); p=win32gui.ClientToScreen(k,(0,0))
            out["children"].append({"hwnd":int(k),"cls":win32gui.GetClassName(k),
                "client_origin":list(p),"client_size":[r[2],r[3]],
                "win_rect":list(win32gui.GetWindowRect(k)),
                "exstyle":hex(win32gui.GetWindowLong(k,win32con.GWL_EXSTYLE)),
                "area":r[2]*r[3]})
    return out

rows=[]
for i in range(3):
    rows.append(snap())
    if i<2: time.sleep(1)
print(json.dumps(rows,ensure_ascii=False,indent=1))
