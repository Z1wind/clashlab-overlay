# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
def c(s): return BT + s + BT

doc = '''# 识别模型还要不要继续做？（2026-11-26 评估）

结论：**分类模型不再需要继续投入**；保留 checkpoint 作实验资产即可。真正卡住自动化的不是分类，是**检测**。

## 现有事实

| 环节 | 现状 | 证据 |
|---|---|---|
| 建筑检测（屏幕上找建筑、给框） | **不可用** | docs/ML_FEASIBILITY.md：逐栋命中 0.06–0.16；70px 人工标注审计至少 42% 错标 |
| 类型分类（给定裁剪） | 可用 | 473 栋补标重训 within 0.879 / LOBO 0.820；仅防御 0.880 / 0.809 |
| 类型+等级（合成素材） | 合成域可用，真实域未验证 | type 0.979 / level MAE 1.14（14,880 合成样本） |
| 运行时实际用到的布局 | layout.json / 人工标注 | 面板/推演/2D 全部读 layout，不依赖模型 |

## 为什么不需要继续做分类

1. **没有检测器，分类器就没有输入**：运行时没有「屏幕→建筑框」的可靠链路，再高的分类精度也用不上。
2. **等级问题已经由 API 解决**：对手名字/部落 → TH 与部落战成员 TH（cocapi），不依赖视觉等级识别。
3. **提升空间有限**：473 栋、32 类，within 0.879 已接近标注噪声上限（人工标注本身有错标）。
4. **成本收益不划算**：继续堆分类精度（更多标注、更长训练）不会让程序自动跑起来；瓶颈在检测与数据。

## 如果要做「全自动导入」，正确投资顺序

1. **检测器**：用 ClashKing 逐级立绘做合成检测训练（贴到真实背景 + 随机布局），再用 1–2 张真实截图人工框验证；GPU 可训，预计数小时；这是唯一能替代手工标注的路径。
2. **标注工具加速**：APK 已经能补标；可再加「点格子后自动猜类型」（分类模型在这里才有用）。
3. **不要**继续单独训练分类/等级模型——除非检测器先成立。

## 现状建议

- 冻结 models/recog_27px.pt、models/v2_*、models/synth_level.pt（作为实验资产，推理接口保留）；
- 主线投入：cocapi 自动等级（已通）、OCR 对手识别（已通）、APK 补标、面板/推演/推荐；
- 只有当你决定做「全自动识别」时，再开检测器任务。
'''.replace("@@@", BT)
open(os.path.join(BASE, "docs", "RECOG_DECISION.md"), "w", encoding="utf-8", newline="\n").write(doc)

# README 最近更新加两条
p = os.path.join(BASE, "README.md")
t = open(p, encoding="utf-8").read()
add = ("- **对手识别（OCR+API）**：截图左上角 OCR 出对手名字/部落 → ClashKing 公开 API（fresh=True 强制回源）→ 玩家 tag/TH/部落战成员 TH；见 "
       + c("docs/OCR_OPPONENT.md") + "。\n"
       "- **exe 内置 OCR**：ClashOverlay.exe 现内置 RapidOCR/onnxruntime（体积 +31MB），新增 "
       + c("--ocr-selftest IMAGE OUT.json") + " 离线自检开关。\n"
       "- **识别模型评估**：分类模型不再继续投入（检测才是瓶颈），结论见 " + c("docs/RECOG_DECISION.md") + "。\n")
anchor = "## 最近更新（2026-11-26）\n\n"
if "对手识别（OCR+API）" not in t:
    t = t.replace(anchor, anchor + add, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("README updated")

p2 = os.path.join(BASE, "CHANGELOG.md")
t2 = open(p2, encoding="utf-8").read()
if "OCR" not in t2:
    add2 = ("- OCR 对手识别（RapidOCR）+ ClashKing API 自动解析 TH/部落战 + fresh=True 最新数据；\n"
            "- exe 内置 OCR（约 121MB）+ --ocr-selftest；识别模型评估结论（docs/RECOG_DECISION.md）。\n")
    t2 = t2.replace("## v0.3.0 (unreleased)\n", "## v0.3.0 (unreleased)\n" + add2, 1)
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("CHANGELOG updated")
