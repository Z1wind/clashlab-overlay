<div align="center">

# ClashLab · 以 LLM 为辅助的部落冲突布阵研究器

**进程外 · 零注入 · 只看画面**：侦察图 → 44×44 标定 → 防守评分 → 弱点 → 战术图/推演。

[![License: MIT](https://img.shields.io/badge/license-MIT-3da639.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-3776ab.svg)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078d4.svg)]()
[![Tests](https://img.shields.io/badge/tests-86%20passing-brightgreen.svg)]()
[![Release](https://img.shields.io/badge/release-v0.1.0-blue.svg)](https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.1.0)

[中文](README.md) · [English](README.en.md) · [教程](docs/教程.md) · [Tutorial](docs/TUTORIAL_en.md)

</div>

> **100% 开源**：代码、数据、文档全在仓库，MIT 许可；无遥测、无服务器、无账号、无游戏注入。

![PANEL](docs/screenshots/panel.png)

一些作者的话:
   现阶段含有大量未完成内容和bug，等待修复，后续我也会接着上传。
   所以恳请各位大佬能够检查该项目或者以此灵感进行自己项目的编写，这样会让我知道我的努力没有白费。

## ✨ 能力

- 🖥 **覆盖层**：HUD 标注（鼠标穿透）/ PANEL 四页（研究/阵型/采集/设置）
- 🎯 **标定**：44×44 DLT 单应，窗口尺寸变化 >10% 自动重标定
- 📊 **评分**：7 指标 → 0–100 + S–F + 带方位的弱点
- 🧠 **战术**：弱点进简报、LLM 提示与面板；女王穿云箭战术图；2D 推演候选落点

## 🚀 快速开始

```powershell
git clone https://github.com/Z1wind/clashlab-overlay.git
cd clashlab-overlay
python -m pip install -r requirements.txt
python run_overlay.py --show --mode HUD --always-on-top --run-seconds 8
python -m unittest discover -s tests   # 86 tests
```

## ⬇️ 下载

- [Release v0.1.0](https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.1.0)：`ClashOverlay.exe`（Windows x64）/ 源码包 / `SHA256SUMS.txt`

## 📊 评分指标

| 指标 | 权重 | 可信度 |
|---|---|---|
| 大本营保护 / 对空 / 对地 / 入口 | 3/2/2/1 | ✅ |
| 资源仓保护 | 2 | ✅（纯防御标注 N/A） |
| 隔间质量 / 墙体效率 | 2/1 | ⚠️ 墙数据未补全，N/A |

## 🧩 架构

```text
LDPlayer 1280x720 --PrintWindow--> frame + 44x44 homography
        --> score / weak points / ring / simulation --> ImGui overlay + PNG
```

## ⚠️ 已知限制

- 识别：27px 同档 0.523，检测不可用；高倍档人工标注曾 ≥42% 错标；
- 墙线自动提取未通过 → 隔间/墙体指标 N/A；
- 视觉大模型：OCR 可用（资源数字 4/4），建筑分类仅 3/16；
- 仅 Windows + 雷电 1280×720 实测。

## 🔒 隐私

不注入、不读内存、不连游戏服务器；仓库不含密钥（LLM 凭据来自本机配置或环境变量）。

## 🙏 致敬与信息来源

完整清单（借用内容/作者/许可证）见 **[ATTRIBUTIONS.md](ATTRIBUTIONS.md)**。主要致敬：

- [@koniz-dev](https://github.com/koniz-dev) · [clash-blueprint-engine](https://github.com/koniz-dev/clash-blueprint-engine)：防守评分 7 指标与弱点体系
- [@Peter537](https://github.com/Peter537) · [clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator)：几何校验与尺寸目录
- [@ClashKingInc](https://github.com/ClashKingInc/ClashKingAssets)、[@chiefpansancolt](https://github.com/chiefpansancolt)、[@Statscell](https://github.com/Statscell)：素材与数据参考
- [FICTURE7/CoCSharp](https://github.com/FICTURE7/CoCSharp)、[DFanso/coc-attack-bot](https://github.com/DFanso/coc-attack-bot) 等：读过未采用，但影响设计判断

## 📄 许可证

MIT（见 [LICENSE](LICENSE)）。第三方署名见 ATTRIBUTIONS；游戏素材遵循 Supercell Fan Content Policy。

## ⚖️ 免责

仅供学习研究。请遵守 Supercell 服务条款；使用后果自负。
