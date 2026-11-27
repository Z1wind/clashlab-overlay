# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT
lines = [
 "",
 "## 2026-11-27 B 救活：建筑门控 + 位置候选（类型待选）",
 "",
 "- 新增 " + c("tools/build_bg_negatives.py") + "：从 105 张真实截图边缘采样 4,470 张背景裁剪（datasets/bg_negatives/imgs.npy）",
 "- 新增 " + c("tools/train_building_gate.py") + "：合成建筑正样本 + 真实背景负样本训练二分类门控；val_acc 0.9988（混淆 [[399,1],[1,1199]]），模型 models/building_gate.pt",
 "- auto_candidates 支持 gate_only 模式：1465 个滑窗 -> 69 个门控通过 -> 去重后 **17 个位置候选**（位置基本正确；类型仍不可靠）",
 "- 标注器页面「自动候选」改为「位置候选」：先选类型，再点蓝框落位；点接受即写入 buildings",
 "- /save 时追加 " + c("out/annotate/_train_manifest.jsonl") + "（图路径/建筑数/墙数/quad），为后续真实负样本训练积累",
 "- E2E：/candidates gate_only=true -> ok=True items=17（gate_conf 0.998~0.9999）",
]
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
if "建筑门控" not in t:
    open(p, "w", encoding="utf-8", newline="\n").write(t.rstrip() + "\n" + "\n".join(lines) + "\n")
    print("STATUS updated")
