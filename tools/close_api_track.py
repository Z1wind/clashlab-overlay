# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT

# 1) STATUS：关闭 API 线 + 记录原因
p = os.path.join(BASE, "docs", "STATUS.md")
t = open(p, encoding="utf-8").read()
add = ("\n## ❌ 2026-11-27：ClashKing / CoC API 通道关闭\n\n"
       "ClashKing（Clash.Ninja）管理员明确回复：**模拟器使用本身是灰色地带、覆盖层可能违反 Supercell ToS**，"
       "且本项目不属于「通过官方 API 使用官方数据的常规工具」，因此**不提供 API/token 权限**。\n\n"
       "- 决定：**不再申请 token、不接布局库**；" + c("cocapi.py") + " 的 token 接口保留代码但标注为「不再推进」；\n"
       "- 仅保留公开端点（玩家名→tag/TH、部落战成员）作为**可选**能力，是否使用由使用者自行评估；\n"
       "- 项目主线转为**纯本地**：截图 → 标定 → 评分/推演/战术图，不依赖第三方授权。\n")
if "API 通道关闭" not in t:
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("STATUS updated")

# 2) CLASHKING.md：顶部加关闭说明，申请模板标注作废
p2 = os.path.join(BASE, "docs", "CLASHKING.md")
t2 = open(p2, encoding="utf-8").read()
note = ("> ⚠️ **2026-11-27 更新：此方向已关闭。** ClashKing（Clash.Ninja）管理员明确表示："
        "模拟器属灰色地带、覆盖层可能违反 Supercell ToS，且本项目不是「通过官方 API 使用官方数据的常规工具」，"
        "因此不授予 API 权限。本项目**不再申请 token、不再接入布局库**；仅保留公开端点作为可选能力。\n\n")
if "此方向已关闭" not in t2:
    t2 = note + t2
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("CLASHKING.md updated")

p3 = os.path.join(BASE, "docs", "CLASHKING_APPLICATION.md")
t3 = open(p3, encoding="utf-8").read()
if t3 and not t3.startswith("> **作废"):
    open(p3, "w", encoding="utf-8", newline="\n").write(
        "> **作废（2026-11-27）**：ClashKing 已明确拒绝（模拟器/覆盖层属 ToS 灰色地带）。本文件仅作记录，请勿再提交申请。\n\n" + t3)
    print("application template marked obsolete")

# 3) README 免责声明增强
p4 = os.path.join(BASE, "README.md")
t4 = open(p4, encoding="utf-8").read()
add4 = ("\n> **非官方工具 / Unofficial tool**：本项目与 Supercell 无关联。覆盖层类工具在部分场景（尤其官方赛事）"
        "可能违反游戏 ToS；模拟器使用亦属灰色地带。请自行评估风险，勿用于竞技赛事或任何可能损害他人的场景。\n")
if "非官方工具 / Unofficial tool" not in t4:
    anchor = "> **100% 开源**"
    t4 = t4.replace(anchor, add4 + "\n" + anchor, 1)
    open(p4, "w", encoding="utf-8", newline="\n").write(t4)
    print("README disclaimer added")

# 4) CHANGELOG
p5 = os.path.join(BASE, "CHANGELOG.md")
t5 = open(p5, encoding="utf-8").read()
add5 = "- 2026-11-27：ClashKing/CoC API 通道关闭（对方明确拒绝：模拟器+覆盖层属 ToS 灰色地带）；项目转为纯本地分析主线。\n"
if "API 通道关闭" not in t5:
    t5 = t5.replace("## v0.3.0 (unreleased)\n", "## v0.3.0 (unreleased)\n" + add5, 1)
    open(p5, "w", encoding="utf-8", newline="\n").write(t5)
    print("CHANGELOG updated")
