# -*- coding: utf-8 -*-
# recog_insp.py — 盘点 blocks/b00..b14：尺寸、接触表、每块缩略图（纯离线只读）
import json, os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK = os.path.join(ROOT, "out", "overlay", "blocks")
OUT = os.path.join(ROOT, "tools", "base_out")
os.makedirs(OUT, exist_ok=True)
log = json.load(open(os.path.join(BLK, "collect_log.json"), encoding="utf-8"))
tiles = []
for t in log["tiles"]:
    p = os.path.join(BLK, t["file"])
    im = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
    tiles.append((t["file"], im, t["cx"], t["cy"]))
    print(t["file"], im.shape, "place=", round(t["cx"], 1), round(t["cy"], 1))

# 接触表：5列 x 3行，每块缩放至 360px 宽
cols, rows = 5, 3
cw = 360
sheet = np.full((rows * 260, cols * cw, 3), 30, np.uint8)
for i, (f, im, cx, cy) in enumerate(tiles):
    r, c = divmod(i, cols)
    h, w = im.shape[:2]
    s = cw / w
    small = cv2.resize(im, (cw, int(h * s)), interpolation=cv2.INTER_AREA)
    rh = small.shape[0]
    y0 = r * 260
    sheet[y0:y0 + rh, c * cw:(c + 1) * cw] = small
    cv2.putText(sheet, f"{f} {w}x{h}", (c * cw + 6, y0 + 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
cv2.imencode(".png", sheet)[1].tofile(os.path.join(OUT, "blocks_contact.png"))
print("contact saved", sheet.shape)
