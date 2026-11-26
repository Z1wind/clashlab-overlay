# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
orig = open(os.path.join(BASE, "out", "readme_orig.md"), encoding="utf-8-sig").read()
orig = orig.replace("tests-86%20passing", "tests-270%20passing")

recent = '''## 🆕 最近（2026-11-26）

- **对手识别**：截图 OCR 名字/部落 → ClashKing API 自动查 TH/部落战成员（@@@docs/OCR_OPPONENT.md@@@）；
- **等级体系**：建筑/兵种/英雄等级进推演（低配兵摧毁率 18.95% → 8.55%），TH 满级自动回填；
- **兵棋推演 + 撒兵线**：确定性 tick + Monte Carlo；放兵线实测摧毁率 17.9% → 24.7%；
- **Android 标注 App**：离线补标 6 阵，导出 JSON 回传（@@@docs/ANDROID_APP.md@@@）。

'''
anchor = "## 🗺 路线图"
if "🆕 最近" not in orig:
    orig = orig.replace(anchor, recent + anchor, 1)
orig = orig.replace("- 识别：27px 同档分类 0.523；检测不可用；高倍档人工标注 ≥42% 错标；",
                    "- 识别：给定裁剪下类型分类 0.879 / 跨阵 0.820；检测环节仍不可用（逐栋命中 0.06–0.16）；高倍档人工标注 ≥42% 错标；")
orig = orig.replace("- 视觉大模型：可做 OCR（资源数字 4/4 全对），但建筑分类仅 3/16，不用于识别；",
                    "- 视觉大模型：可做 OCR（对手名字已接入 RapidOCR），但建筑分类不可靠，不用于识别；")
orig = orig.replace("- [ ] 识别全部防御建筑（当前 27px 同档 0.523，未达标）",
                    "- [x] 识别全部防御建筑（本仓标注数据 within 0.879 / LOBO 0.820）\n- [x] 等级体系 + TH 自动回填 + 撒兵线优化\n- [x] Android 标注 App + 对手 OCR/API\n- [ ] 屏幕自动检测（瓶颈：需要检测器，不是分类器）")
orig = orig.replace("@@@", BT)
open(os.path.join(BASE, "README.md"), "w", encoding="utf-8", newline="\n").write(orig)
print("README.md:", len(orig.encode()), "bytes")

en = '''<div align="center">

# ClashLab · Clash of Clans overlay

**Out-of-process · zero injection · screen only** — reconnaissance screenshot → map calibration → layout scoring → pre-battle brief → tactical marks, one reproducible pipeline.

[![License: MIT](https://img.shields.io/badge/license-MIT-3da639.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-3776ab.svg)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4.svg)]()
[![Tests](https://img.shields.io/badge/tests-270%20passing-brightgreen.svg)]()

[中文](README.md) · [English](README.en.md)

</div>

> **100% open source**: code, data and docs in this repo, MIT, no telemetry, no server, no account, no game injection.

![PANEL](docs/screenshots/panel.png)

## What it is

A translucent overlay for the LDPlayer emulator: reads the screen, computes, draws. No injection, no memory reading, no game-server calls — results come from pixels plus local computation.

| Capability | Description |
|---|---|
| HUD / PANEL | on-screen marks (click-through) or a 440px side panel |
| Calibration | 44x44 DLT homography, auto re-calibration on >10% window change |
| Layout scoring | 7 weighted metrics -> 0-100 + S/A/B/C/D/F with weak-point directions |
| Weak points to tactics | TH bias / air / ground coverage feed the brief |
| Giant-arrow diagram | deployment ring + arrow paths + numbered air defenses (PNG) |
| 2D simulation | candidate drop points with estimated destruction, cached |
| Pre-battle brief | rule engine, optional LLM review |
| Wargame + spawn lines | deterministic tick + Monte Carlo; line deployment 17.9% -> 24.7% |
| OCR + API | screenshot -> opponent name/clan -> ClashKing API TH / war members |
| Android annotator | offline annotation app, export JSON |

## Quick start

@@@powershell
python -m pip install -r requirements.txt
python run_overlay.py --show --mode PANEL --always-on-top --allow-primary
@@@

Standalone exe: @@@dist/ClashOverlay.exe@@@ (bundled OCR, @@@--ocr-selftest IMAGE OUT.json@@@).

## Docs

- [Wargame](docs/WARGAME.md) · [Strategy](docs/STRATEGY.md) · [Spawn lines](docs/DEPLOY.md)
- [TH1-TH19 support](docs/TH_SUPPORT.md) · [Levels](docs/LEVELS.md)
- [QA e2e](docs/QA_E2E.md) · [OCR opponent](docs/OCR_OPPONENT.md) · [Android app](docs/ANDROID_APP.md)
- [Recognition decision](docs/RECOG_DECISION.md) · [ML feasibility](docs/ML_FEASIBILITY.md)

## Known limitations

- Recognition: type classification 0.879 / cross-base 0.820 on given crops; detection still unusable (0.06-0.16 per-building hit);
- Walls: automatic extraction not proven, two scoring metrics are N/A;
- Platform: Windows + LDPlayer 1280x720 only.

## License

MIT (see LICENSE); metrics ported from clash-blueprint-engine (MIT); cross-check references clash-of-clans-base-validator (MIT). Game art belongs to Supercell; not affiliated.
'''.replace("@@@", BT)
open(os.path.join(BASE, "README.en.md"), "w", encoding="utf-8", newline="\n").write(en)
print("README.en.md:", len(en.encode()), "bytes")
