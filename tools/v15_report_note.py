# -*- coding: utf-8 -*-
# v15_report_note.py — 给 stitch_max_report.json 补状态。新文件。
import json,os
R=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
p=os.path.join(R,"stitch_max_report.json")
d=json.load(open(p,encoding="utf-8"))
d["status"]="REJECTED"
d["status_note"]=("54块max帧已采并取中值(max/b_c*r*.png)；但盲拍步长在sendevent下衰减，"
 "命令几何(600h/240v)摆放与真实位移不符；ORB/RANSAC在贫瘠荒野与重复墙段退化，"
 "多数邻边无法估计平移，相位相关未启用。recon_full_max_raw.png为未对齐草稿，不可用作全基地图，已弃用。"
 "缝残差仅ORB内点中位，非拼接误差。")
d["blocks_captured"]=54
d["grid_intended"]="9行x6列(实际步长不恒定)"
json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("ok")
