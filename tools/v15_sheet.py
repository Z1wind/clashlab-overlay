# -*- coding: utf-8 -*-
# v15_sheet.py — 每行6块拼接触表，供人工清点。新文件。
import os,cv2,numpy as np,sys
R=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon";M=os.path.join(R,"max")
r=int(sys.argv[1])
tiles=[]
for c in range(6):
    p=os.path.join(M,f"b_c{c}r{r}.png")
    im=cv2.imdecode(np.fromfile(p,dtype=np.uint8),1)
    im=cv2.resize(im,(427,240))
    cv2.putText(im,f"c{c}r{r}",(8,24),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2)
    tiles.append(im)
row1=np.hstack(tiles[:3]);row2=np.hstack(tiles[3:])
sheet=np.vstack([row1,row2])
cv2.imencode(".png",sheet)[1].tofile(os.path.join(R,f"sheet_r{r}.png"))
print("ok",sheet.shape)
