# -*- coding: utf-8 -*-
"""生成一张可控的仿真阵型图，用于在没有游戏账号时验证视觉与规划链路。"""
import numpy as np
from PIL import Image, ImageDraw

from .geo import Calib, tile_to_screen
from .sim import Simulator

SIZE = (1280, 720)
N = 44
KX = 13.4
KY = 6.7

BUILDINGS = [
    ("大本营", (22, 22), 6000, 0, 0.0, False),
    ("鹰火炮", (22, 15), 4500, 350, 11.0, False),
    ("地狱塔", (16, 22), 4200, 120, 7.0, False),
    ("地狱塔", (28, 22), 4200, 120, 7.0, False),
    ("X连弩", (22, 29), 4000, 180, 11.0, False),
    ("X连弩", (18, 28), 4000, 180, 11.0, False),
    ("法师塔", (14, 17), 2600, 260, 7.0, True),
    ("法师塔", (30, 17), 2600, 260, 7.0, True),
    ("法师塔", (14, 27), 2600, 260, 7.0, True),
    ("法师塔", (30, 27), 2600, 260, 7.0, True),
    ("迫击炮", (12, 22), 2400, 200, 10.0, True),
    ("迫击炮", (32, 22), 2400, 200, 10.0, True),
    ("箭塔", (17, 11), 1800, 120, 10.0, False),
    ("箭塔", (27, 11), 1800, 120, 10.0, False),
    ("箭塔", (11, 18), 1800, 120, 10.0, False),
    ("箭塔", (11, 26), 1800, 120, 10.0, False),
    ("箭塔", (33, 18), 1800, 120, 10.0, False),
    ("箭塔", (33, 26), 1800, 120, 10.0, False),
    ("加农炮", (13, 13), 1600, 110, 9.0, False),
    ("加农炮", (31, 13), 1600, 110, 9.0, False),
    ("加农炮", (13, 31), 1600, 110, 9.0, False),
    ("加农炮", (31, 31), 1600, 110, 9.0, False),
    ("防空", (20, 12), 1400, 0, 10.0, False),
    ("防空", (24, 32), 1400, 0, 10.0, False),
    ("部落城堡", (22, 34), 3000, 0, 0.0, False),
]


def ground_truth_quad(cx=640, cy=360):
    pts = [tile_to_screen(0, 0, cx, cy, KX, KY, N),
           tile_to_screen(N, 0, cx, cy, KX, KY, N),
           tile_to_screen(N, N, cx, cy, KX, KY, N),
           tile_to_screen(0, N, cx, cy, KX, KY, N)]
    return np.array(pts, dtype=np.float32)


def make_demo():
    W, H = SIZE
    cx, cy = W // 2, H // 2
    img = Image.new("RGB", SIZE, (26, 30, 26))
    d = ImageDraw.Draw(img)

    quad = ground_truth_quad(cx, cy)
    d.polygon([tuple(p) for p in quad], fill=(96, 132, 78))

    # 网格
    for g in range(0, N + 1, 4):
        d.line([tile_to_screen(g, 0, cx, cy, KX, KY, N),
                tile_to_screen(g, N, cx, cy, KX, KY, N)], fill=(88, 122, 72), width=1)
        d.line([tile_to_screen(0, g, cx, cy, KX, KY, N),
                tile_to_screen(N, g, cx, cy, KX, KY, N)], fill=(88, 122, 72), width=1)

    # 城墙：一个格里方环
    wall_tiles = []
    for g in range(9, 36):
        wall_tiles += [(g, 9), (g, 35), (9, g), (35, g)]
    for gx, gy in wall_tiles:
        p = tile_to_screen(gx, gy, cx, cy, KX, KY, N)
        d.rectangle([p[0] - 5, p[1] - 3, p[0] + 5, p[1] + 3], fill=(150, 148, 140))

    # 建筑
    for name, tile, hp, dps, rng, splash in BUILDINGS:
        p = tile_to_screen(tile[0], tile[1], cx, cy, KX, KY, N)
        s = 15 if name == "大本营" else 11
        d.rectangle([p[0] - s, p[1] - s * 0.8, p[0] + s, p[1] + s * 0.8],
                    fill=(214, 196, 152) if name == "大本营" else (196, 188, 172),
                    outline=(58, 58, 58))

    # 红色禁区：内圈（与游戏一致，覆盖建筑与地面）
    inner = [tile_to_screen(6, 6, cx, cy, KX, KY, N),
             tile_to_screen(38, 6, cx, cy, KX, KY, N),
             tile_to_screen(38, 38, cx, cy, KX, KY, N),
             tile_to_screen(6, 38, cx, cy, KX, KY, N)]
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.polygon([tuple(p) for p in inner], fill=(222, 34, 34, 115))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    frame = np.array(img)[:, :, ::-1].copy()  # RGB -> BGR

    sim = Simulator(N)
    for name, tile, hp, dps, rng, splash in BUILDINGS:
        sim.add_building(name, tile, hp, dps, rng, splash)
    sim.add_wall(wall_tiles)

    calib = Calib.from_quad(quad, n=N)
    return frame, sim, calib, quad


def ring_mask(n=N, band=7):
    m = np.zeros((n + 1, n + 1), dtype=bool)
    m[:, :] = True
    m[band:n + 1 - band, band:n + 1 - band] = False
    return m
