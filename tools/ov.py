import cv2, numpy as np, os
p=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\v6_stitched_base.png"
img=cv2.imdecode(np.fromfile(p,np.uint8),cv2.IMREAD_COLOR)
h,w=img.shape[:2]
s=1500/w
ov=cv2.resize(img,(1500,int(h*s)),interpolation=cv2.INTER_AREA)
out=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\tools\base_out\overview.png"
cv2.imencode(".png",ov)[1].tofile(out)
print(img.shape, ov.shape)
