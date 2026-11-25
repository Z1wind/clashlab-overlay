# -*- coding: utf-8 -*-
# v10 只读：枚举 LDPlayerMainFrame 及后代，报 RenderWindow 客户区原点/尺寸（每次现算，不写死）
import win32gui, json, sys

def find_main():
    out = []
    def _cb(h, _):
        if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
            out.append(h)
    win32gui.EnumWindows(_cb, None)
    return out[0] if out else None

h = find_main()
res = {"main": None, "children": []}
if h:
    cr = win32gui.GetClientRect(h)
    pt = win32gui.ClientToScreen(h, (0, 0))
    res["main"] = {"hwnd": int(h), "client_origin": list(pt),
                   "client_size": [cr[2], cr[3]], "win_rect": list(win32gui.GetWindowRect(h))}
    allc = []
    def collect(k):
        sub = []
        win32gui.EnumChildWindows(k, lambda x, _: sub.append(x), None)
        for x in sub:
            allc.append(x); collect(x)
    collect(h)
    for k in allc:
        if win32gui.IsWindowVisible(k):
            r = win32gui.GetClientRect(k); p = win32gui.ClientToScreen(k, (0, 0))
            res["children"].append({"hwnd": int(k), "cls": win32gui.GetClassName(k),
                                   "client_origin": list(p), "client_size": [r[2], r[3]],
                                   "win_rect": list(win32gui.GetWindowRect(k))})
print(json.dumps(res, ensure_ascii=False, indent=1))
