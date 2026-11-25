# -*- coding: utf-8 -*-
"""半自动标注：在截图上点选建筑，生成布局 JSON。

交互（都在一个可拖拽的窗口里，不接管游戏）：
  左键点击 = 放一个当前类型的建筑（自动换算成 44x44 瓦片坐标）
  1..9     = 切换建筑类型（顺序见顶部提示）
  空格     = 删除最后一次放置
  S        = 保存并退出
  Esc      = 退出不保存
"""
import json
import os
import tkinter as tk

from PIL import Image, ImageTk

from . import assets, vision
from .geo import Calib
from .render import font

PALETTE = ["town-hall", "eagle-artillery", "scattershot", "inferno-tower", "x-bow",
           "air-defense", "wizard-tower", "archer-tower", "cannon", "mortar", "defense"]


def run_annotate(image_path, save_path, grid=44):
    frame = vision.imread(image_path)
    if frame is None:
        raise SystemExit(f"读不到图片：{image_path}")
    info, calib = vision.analyze_frame(frame, focus="offline")
    if calib is None:
        raise SystemExit("这张图没能标定出地图外框，换一张完整阵型的截图")
    quad = info["boundary"]["quad"]
    calib = Calib.from_quad(quad, n=grid)

    root = tk.Tk()
    root.title("ClashLab 标注")
    scale = min(1.0, 1280 / frame.shape[1])
    img = Image.fromarray(frame[:, :, ::-1]).resize(
        (int(frame.shape[1] * scale), int(frame.shape[0] * scale)), Image.LANCZOS)
    tkimg = ImageTk.PhotoImage(img)
    canvas = tk.Canvas(root, width=img.size[0], height=img.size[1], highlightthickness=0)
    canvas.pack()
    canvas.create_image(0, 0, anchor="nw", image=tkimg)

    state = {"type": 0, "marks": []}

    def banner(_=None):
        canvas.delete("hint")
        txt = "  ".join(f"{i + 1}:{assets.STATS.get(t, {}).get('cn', t)}" for i, t in enumerate(PALETTE))
        canvas.create_rectangle(0, 0, img.size[0], 24, fill="#0c1013", outline="", tags="hint")
        canvas.create_text(8, 12, anchor="w", text=f"[{PALETTE[state['type']]}]  {txt}",
                           fill="#eef0f2", font=font(12), tags="hint")

    def draw_quad():
        canvas.delete("quad")
        canvas.create_line(*[c for p in quad for c in (p[0] * scale, p[1] * scale)] + [quad[0][0] * scale, quad[0][1] * scale],
                           outline="#f0c452", width=1, tags="quad")

    def on_key(e):
        if e.keysym in [str(i + 1) for i in range(len(PALETTE))]:
            state["type"] = int(e.keysym) - 1
            banner()
        elif e.keysym == "space" and state["marks"]:
            m = state["marks"].pop()
            canvas.delete(m)
        elif e.keysym.lower() == "s":
            save()
        elif e.keysym == "Escape":
            root.destroy()

    def on_click(e):
        sx, sy = e.x / scale, e.y / scale
        gx, gy = calib.px_to_tile(sx, sy)
        if not (-0.5 <= gx <= grid + 0.5 and -0.5 <= gy <= grid + 0.5):
            return
        t = PALETTE[state["type"]]
        r = 9
        item = canvas.create_oval(e.x - r, e.y - r, e.x + r, e.y + r, fill="#60c882", outline="#12351f")
        canvas.create_text(e.x, e.y, text=str(len(state["marks"]) + 1), fill="#0d2415", font=font(10, True))
        canvas.create_text(e.x + 12, e.y - 10, text=assets.STATS.get(t, {}).get("cn", t),
                           fill="#f0c452", font=font(10), anchor="w")
        state["marks"].append({"item": item, "type": t, "tile": [round(gx, 1), round(gy, 1)]})

    def save():
        items = [{"type": m["type"], "tile": m["tile"]} for m in state["marks"]]
        data = {"name": os.path.basename(image_path), "grid": grid, "buildings": items,
                "source": {"image": image_path, "quad": quad}}
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存 {save_path}（{len(items)} 个建筑）")
        root.destroy()

    canvas.bind("<Button-1>", on_click)
    root.bind("<Key>", on_key)
    banner()
    draw_quad()
    root.mainloop()
    return save_path


if __name__ == "__main__":
    run_annotate(r"out\live_00.png", r"layouts\layout.json")
