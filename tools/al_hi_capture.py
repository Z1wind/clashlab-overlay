# -*- coding: utf-8 -*-
"""高倍视野下分屏抓图：按网格平移相机，每屏存一张（供人工标注）。"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import al_drive as d

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label", "hi")
os.makedirs(OUT, exist_ok=True)

CX, CY = 640, 380


def drag(dx, dy, ms=500):
    d.swipe(CX, CY, CX - dx, CY - dy, ms)
    time.sleep(0.6)


def main():
    n = 0
    shots = []
    for row in range(2):
        for col in range(3):
            p = os.path.join(OUT, "h%d%d.png" % (row, col))
            d.shot(p)
            shots.append(p)
            n += 1
            if col < 2:
                drag(620, 0)
        if row < 1:
            drag(0, 330)
            drag(-620, 0)
        time.sleep(0.2)
    print("shots=%d" % n)


main()
