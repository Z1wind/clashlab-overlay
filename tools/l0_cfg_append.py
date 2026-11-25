# -*- coding: utf-8 -*-
# 纯离线：config 仅追加 L0_snapped_v3 测量记录，旧键全保留；不改 v2.status
import json, os, datetime
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
P=os.path.join(ROOT,"config","view_quads.json")
qj=json.load(open(P,encoding="utf-8"))
qj["L0_snapped_v3"]={
 "based_on":"L0_snapped_v2",
 "mode":"offline independent error quantification (no adb/no screen)",
 "footprint_visual_span":{
   "reads":[
     {"name":"金仓NE","span_px":70,"tiles":3,"ppt":23.33},
     {"name":"金仓SW","span_px":70,"tiles":3,"ppt":23.33},
     {"name":"金仓SE","span_px":72,"tiles":3,"ppt":24.00},
     {"name":"金仓S","span_px":70,"tiles":3,"ppt":23.33},
     {"name":"法师塔SE","span_px":66,"tiles":3,"ppt":22.00}
   ],
   "mean_ppt":23.20,
   "vs24_dev_pct":-3.33,
   "caveat":"L0(≈24px/格)底面轮廓不可辨,读数为机身视觉跨度(容差±8px),非严格底面边,不作常量表依据"
 },
 "v2_self_residual":{
   "handread_mean_g":0.451,"handread_mean_px":10.8,
   "handread_max_g":0.593,"handread_max_px":14.2,
   "anchor_diag_mean_g":0.342,"anchor_diag_max_g":0.594,
   "note":"手读点余量=手读中心到v2最近格点距离,含手读噪声(±10px),非独立真值误差;锚点诊断非真值"
 },
 "independent_truth":"unavailable: canvas横向39.6格<44,平台左右缘裁切,外围草地/围墙未入镜,墙行不可计数,底面不可辨",
 "verdict":"near_unverified",
 "status":"near",
 "no_usable_v1":"独立尺度①与独立格位真值②在本画布不可得,不满足usable_v1证据",
 "correction_path":"横向补采(左右各外扩约4-8格)使四边入镜后直测;或换更近档(更大tile_px)单帧直测底面",
 "ts":datetime.datetime.now().isoformat(timespec="seconds")
}
json.dump(qj,open(P,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("appended L0_snapped_v3; keys:",list(qj.keys()))
