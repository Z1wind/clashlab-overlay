# -*- coding: utf-8 -*-
# 纯离线：仅更新 L0_snapped_v3 字段为 usable_v1；其余键一字节不动
import json, os, datetime
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
P=os.path.join(ROOT,"config","view_quads.json")
qj=json.load(open(P,encoding="utf-8"))
v3=qj["L0_snapped_v3"]
v3["status"]="usable_v1"
v3["verdict"]="usable_v1"
v3["error"]={
  "avg_tile":0.45,"max_tile":0.59,"avg_px":10.8,"max_px":14.2
}
v3["accept_rule"]="用户口径：<1格(24px)即可作 v1 常量表"
v3["caveat"]="①px/格 23.20 为机身视觉跨度估读（容差±8px），非严格底面直测；②格位偏差含±10px 手读噪声，且整数格位基准受横向裁切(39.6格<44)限制，非独立真值；③本表待全阵采集(L0 6张拼接)出图后由直读 quad 取代"
v3["superseded_by"]="L0_full（全阵采集线产出，届时若 verified 则本项降为 reference）"
v3.pop("no_usable_v1",None)
v3["ts"]=datetime.datetime.now().isoformat(timespec="seconds")
json.dump(qj,open(P,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
# 复核
chk=json.load(open(P,encoding="utf-8"))
print("v3.status=",chk["L0_snapped_v3"]["status"])
print("v2.status=",chk["L0_snapped_v2"]["status"])
print("keys=",list(chk.keys()))
