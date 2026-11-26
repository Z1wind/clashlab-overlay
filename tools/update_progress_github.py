# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT

upd_zh = (
"- **类型+等级双头模型（GPU）**：用 ClashKing 逐级立绘合成 14,880 张样本（29 类 / 372 个类型-等级组合），"
"RTX 4060 训练 300 epoch → **type_acc 0.979 / level_mae 1.14**（合成集），产物 " + c("models/synth_level.pt") + "。\n"
"- **数据驱动自动等级**：新增 " + c("clashlab/cocapi.py") + " + " + c("tools/cocapi_cli.py") + "，用 ClashKing 公开 API 按玩家/部落标签拿 **TH 等级**与部落战双方成员 TH（无需 token），并可自动回填布局建筑等级；英雄/兵种等级需官方 API token（接口已预留）。\n"
"- **识别模型重训（473 栋）**：全类 within **0.879** / LOBO **0.820**；仅防御类 within 0.880 / LOBO 0.809（此前 0.718/0.581）。\n"
"- **Android 标注 App v0.2**：强制横屏 + 建筑文字标签（类型+等级）+ 导出 JSON（4,666,248 B，debug 签名）。\n"
"- **等级体系**：建筑/兵种/英雄等级参与推演，实测低配兵摧毁率 18.95% → 8.55%；TH 满级自动回填。\n"
)
p = os.path.join(BASE, "README.md")
t = open(p, encoding="utf-8").read()
anchor = "## 最近更新（2026-11-26）\n\n"
if "类型+等级双头模型（GPU）" not in t:
    t = t.replace(anchor, anchor + upd_zh, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("README zh updated")

upd_en = (
"- **Type+level dual-head model (GPU)**: 14,880 synthetic samples from ClashKing per-level sprites (29 types / 372 type-level combos), 300 epochs on RTX 4060 → **type_acc 0.979 / level_mae 1.14** (synthetic), checkpoint " + c("models/synth_level.pt") + ".\n"
"- **Data-driven auto levels**: " + c("clashlab/cocapi.py") + " + " + c("tools/cocapi_cli.py") + " use ClashKing public API to resolve **TH level** and both clans' member THs from a player/clan tag (no token), and auto-fill building levels; hero/troop levels need an official Supercell token (hook reserved).\n"
"- **Recognition retrain (473 buildings)**: all classes within **0.879** / LOBO **0.820**; defense-only 0.880 / 0.809 (previously 0.718/0.581).\n"
"- **Android annotator v0.2**: landscape + on-map type/level labels + JSON export (4,666,248 B).\n"
"- **Level system**: building/troop/hero levels in the wargame; low-level troops drop destruction 18.95% → 8.55%.\n"
)
p2 = os.path.join(BASE, "README.en.md")
t2 = open(p2, encoding="utf-8").read()
a2 = "## Recent updates (2026-11-26)\n\n"
if "Type+level dual-head model" not in t2:
    t2 = t2.replace(a2, a2 + upd_en, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("README en updated")

p3 = os.path.join(BASE, "CHANGELOG.md")
t3 = open(p3, encoding="utf-8").read()
add = '''## v0.3.0 (unreleased)

- 合成素材「类型+等级」双头模型（GPU 300 epoch）：type_acc 0.979 / level_mae 1.14（合成集）；
- ClashKing 公开 API 客户端：玩家/部落标签 → 自动 TH 等级与部落战成员 TH，自动回填布局等级；
- 识别重训（473 栋，用户 APK 补标后）：全类 within 0.879 / LOBO 0.820；
- Android 标注 App v0.2：横屏 + 建筑类型/等级文字标签 + 导出 JSON；
- 2D 图分类扩展（经济/兵营/陷阱）+ 面板建筑构成行；放兵线/区域优化；TH1–TH19 数据层与等级体系。

'''
if "v0.3.0 (unreleased)" not in t3:
    t3 = t3.replace("## v0.2.0 (unreleased)", add + "## v0.2.0 (unreleased)", 1)
    open(p3, "w", encoding="utf-8", newline="\n").write(t3)
    print("CHANGELOG updated")

p4 = os.path.join(BASE, "docs", "ROADMAP.md")
t4 = open(p4, encoding="utf-8").read()
add4 = '''
## 第五阶段（2026-11-26 晚）

- **等级识别**：ClashKing 逐级立绘 → 合成 14,880 样本 → GPU 双头模型（type 0.979 / level MAE 1.14）；
- **自动等级**：ClashKing 公开 API 取 TH / 部落战成员 TH，自动回填敌方建筑等级（token 可补英雄/兵种等级）；
- **识别重训**：473 栋补标后 within 0.879 / LOBO 0.820；
- **Android App v0.2**：横屏 + 标签 + 导出 JSON；
- 待办：官方 API token 接英雄/兵种等级；真实截图等级验证；APK 真机回归。
'''
if "第五阶段" not in t4:
    t4 = t4.rstrip() + "\n" + add4
    open(p4, "w", encoding="utf-8", newline="\n").write(t4)
    print("ROADMAP updated")
