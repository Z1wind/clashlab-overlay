# -*- coding: utf-8 -*-
# 金仓3x3宽度实测：l1_00 中金仓框 (340,330,560,555)，灰度列投影求实体宽度
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for f in ["l1_00.png"]:
    im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","blocks_L1",f),dtype=np.uint8),cv2.IMREAD_COLOR)
    g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    # 金仓区域 340:560, 330:555 内非草坪像素列
    sub=g[330:555,340:560]
    col=(sub<180).mean(axis=0)
    xs=np.where(col>0.2)[0]
    print(f,"gold storage 实体宽=",xs.max()-xs.min()+1,"px -> 3格=",round((xs.max()-xs.min()+1)/3,1),"px/格")
# 对照 zoom_L1 参考帧金仓（目读位置 x300-480,y250-430）
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY)
sub=g[250:430,300:480]
col=(sub<180).mean(axis=0)
xs=np.where(col>0.2)[0]
print("zoom_L1 ref 该块宽=",xs.max()-xs.min()+1,"px")
