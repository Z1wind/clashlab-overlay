# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
lines = [
 "",
 "## 2026-11-27 战斗日抓图（自主推进收尾）",
 "",
 "- 战斗日 21:47 开始；修好「我军/敌军」切换后，抓到真实战斗日 1080p 阵型截图：",
 "  - out/live/war1080/base_01_215536.png（TH15，4.2MB，1920x1080）",
 "  - base_04_215612.png / base_06_215641.png",
 "- 拼图链路可跑（war_base_montage：37 候选 → NMS 后 13 框），但**固定视角标定仍偏**（裁剪未对准建筑）",
 "- 新尝试：金顶晶格拟合（" + c("tools/gold_lattice_fit2.py") + "）：检出 718 金点，基向量 u≈(17.5,17)/v≈(-17.6,16.4)，残差 0.244（≈随机）→ 未收敛，不采用",
 "- 下一步：用标注器/覆盖层的「点 4 角」人工校准一次真实战场截图（1 分钟），再批量跑候选+标注+微调",
 "",
 "### 本轮自主推进产出汇总",
 "- 一键战报（HTML，面板+/标注器+/CLI）",
 "- 真实图标 39/39 补齐",
 "- 1080p 侦察抓图流水线（OCR 状态机、断线重连、我军/敌军切换）",
 "- 战场拼图/标注→布局→报告 工具链（scout_to_report / war_batch_reports / labels_to_layout / finetune_shot_type）",
 "- 样例报告包 v2（含 3 份战报，316,506 bytes）已上传 v0.3.6",
]
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
if "战斗日抓图（自主推进收尾）" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + "\n".join(lines) + "\n")
    print("STATUS updated")
