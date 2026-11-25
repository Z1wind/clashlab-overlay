<div align="center">

# ClashLab · An LLM-assisted Clash of Clans base-layout research tool

**Out-of-process · zero injection · screen-only**: screenshot → 44×44 calibration → defense score → weak points → tactical diagram / simulation.

[![License: MIT](https://img.shields.io/badge/license-MIT-3da639.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-3776ab.svg)](requirements.txt)
[![Tests](https://img.shields.io/badge/tests-86%20passing-brightgreen.svg)]()
[![Release](https://img.shields.io/badge/release-v0.1.0-blue.svg)](https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.1.0)

[中文](README.md) · [English](README.en.md) · [教程](docs/教程.md) · [Tutorial](docs/TUTORIAL_en.md)

</div>

> **100% open source** — code, data and docs in this repo, MIT. No telemetry, no server, no account, no game injection.

![PANEL](docs/screenshots/panel.png)

## ✨ Features

- 🖥 Overlay: click-through HUD + 4-page PANEL (research / layout / collect / settings)
- 🎯 Calibration: 44×44 DLT homography, auto recalibration on >10% resize
- 📊 Score: 7 metrics → 0–100, S–F grade, located weak points
- 🧠 Tactics: findings into brief / LLM prompt / panel; giant-arrow diagram; 2D simulation

## 🚀 Quick start

```powershell
git clone https://github.com/Z1wind/clashlab-overlay.git
cd clashlab-overlay
python -m pip install -r requirements.txt
python run_overlay.py --show --mode HUD --always-on-top --run-seconds 8
python -m unittest discover -s tests   # 86 tests
```

## ⬇️ Download

- [Release v0.1.0](https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.1.0): `ClashOverlay.exe` (Windows x64), source zip, `SHA256SUMS.txt`

## 📊 Known limitations

- Recognition: 0.523 at 27 px/tile; detection not usable;
- Wall auto-extraction not validated → compartment/wall metrics N/A;
- Vision LLM: OCR OK (4/4), building classification 3/16;
- Verified only on Windows + LDPlayer at 1280×720.

## 🔒 Privacy

No injection, no memory reading, no game-server access. No keys in repo; LLM credentials come from local config or env vars.

## 🙏 Acknowledgements

Full list in **[ATTRIBUTIONS.md](ATTRIBUTIONS.md)**. Main credits: [@koniz-dev](https://github.com/koniz-dev) (clash-blueprint-engine, scoring metrics), [@Peter537](https://github.com/Peter537) (base-validator), [@ClashKingInc](https://github.com/ClashKingInc), [@chiefpansancolt](https://github.com/chiefpansancolt), [@Statscell](https://github.com/Statscell) (assets/data).

## 📄 License

MIT (see [LICENSE](LICENSE)). Game assets follow the Supercell Fan Content Policy.

## ⚖️ Disclaimer

For learning and research only. Follow Supercell's Terms of Service; use at your own risk.
