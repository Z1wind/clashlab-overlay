# -*- coding: utf-8 -*-
# finalize.py — 80px标尺单块 + view_quads.json
import cv2, numpy as np, os, json, datetime
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks3")
# 标尺单块：b15 原始裁块
tile=cv2.imdecode(np.fromfile(os.path.join(BLK,"b15.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
tile=tile[:,:905]  # 去右导轨+按钮
g=tile.copy()
H,W=g.shape[:2]
for x in range(0,W,80):
    cv2.line(g,(x,0),(x,H),(0,180,0),1); cv2.putText(g,str(x),(x+3,18),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,0),1)
for y in range(0,H,80):
    cv2.line(g,(0,y),(W,y),(0,180,0),1); cv2.putText(g,str(y),(3,y+16),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,0),1)
# 80px 标尺条
cv2.line(g,(30,H-40),(110,H-40),(0,0,255),4)
cv2.putText(g,"80px = 1 tile",(30,H-50),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
cv2.imencode(".png",g)[1].tofile(os.path.join(ROOT,"out","overlay","v6_zoom_max_tile.png"))

# 拼接画布尺寸（place.py 输出）
base=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_stitched_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
bh,bw=base.shape[:2]
# quad: T,R,B,L 四角（stitched 画面有效游戏区=画布全幅）
quad=[[0,0],[bw-1,0],[bw-1,bh-1],[0,bh-1]]
cfg={"version":1,"locked":{"1280x720":{"mode":"max_zoom","tile_px":80,
  "tile_px_range":[77,83],
  "quad":quad,"order":"T,R,B,L","source":"stitched@maxzoom",
  "conf":0.95,"blocks":15,"overlap":0.54,
  "screenshot":"out/overlay/v6_stitched_base.png",
  "ts":datetime.datetime.now().isoformat(timespec="seconds"),
  "th":"16"}}}
os.makedirs(os.path.join(ROOT,"config"),exist_ok=True)
json.dump(cfg,open(os.path.join(ROOT,"config","view_quads.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("ruler",g.shape,"quad",quad,"canvas",base.shape)
