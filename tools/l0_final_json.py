# -*- coding: utf-8 -*-
import json, os, time
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
cfg=json.load(open(os.path.join(ROOT,"config","view_quads.json"),encoding="utf-8"))
cfg["fit_resid"]={"A_NE_T-R":4.56,"B_NW_T-L":2.41,"C_SW_L-B":2.56,"D_SE_B-R(观测弱,3段)":0.79}
cfg["d_check_resid_px"]=11.38
cfg["solutions"]={
 "sol1_midpoint_invariant":{"R":cfg["quad"]["R"],"H/W":cfg["HW_ratio"],"note":"中点不变量(T+B)/2=(L+R)/2 解出R; H/W=0.766"},
 "sol2_HW_2to1":{"note":"按H/W=2:1约束与中点不变量冲突, 无共存解; 本档透视下H/W实测<1, 2:1约束不适用, 弃用"}
}
cfg["grid_note"]="L0两屏四边均被裁, quad顶点在画布外; 网格为仿射格网示意, 未完成格位对齐(需交互锚点标定)"
cfg["ts"]=time.strftime("%Y-%m-%dT%H:%M:%S")
json.dump(cfg,open(os.path.join(ROOT,"config","view_quads.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(json.dumps(cfg,ensure_ascii=False,indent=2))
