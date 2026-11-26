<div align="center">

# ClashLab · An LLM-assisted Clash of Clans base layout analyzer

Turn one clean scouting screenshot into a defence score, weak points and tactical diagrams on a 44×44 grid.

[![License: MIT](https://img.shields.io/badge/license-MIT-3da639.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-3776ab.svg)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078d4.svg)]()
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![CI](https://github.com/Z1wind/clashlab-overlay/actions/workflows/ci.yml/badge.svg)](https://github.com/Z1wind/clashlab-overlay/actions/workflows/ci.yml)
[![Release](https://img.shields.io/badge/release-v0.1.0-blue.svg)](https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.1.0)

[中文](README.md) · [English](README.en.md) · [教程](docs/教程.md) · [Tutorial](docs/TUTORIAL_en.md)

</div>

ClashLab is a base layout analyzer for Clash of Clans, built around TH16 base layouts. The pipeline is easy to describe: grab a scouting screenshot from the emulator, calibrate it onto the game's 44×44 grid, serialise what is on screen into a layout JSON, score the base layout, find weak points, then turn the findings into a tactical diagram or a 2D top-down view.

The tool runs entirely out of process as an ImGui overlay next to the LDPlayer window. It does not inject into the game, does not read memory and does not talk to game servers — it only looks at what is on screen. The code is open source under MIT, and the data and docs live in this repository too.

A note before you dig in: this version still has unfinished parts and bugs, and I'm working through them. It is not a finished tool you can take into a clan war yet; it is closer to a workbench for Clash of Clans base layout analysis, building recognition and overlay development.

![PANEL](docs/screenshots/panel.png)

## Recent updates (2026-11-26)

- **Wargame simulation** (`clashlab/wargame.py`): army + spawn -> deterministic tick battle sim + Monte Carlo destruction distribution (base 03 mean 15.5%, best spawn 22.1%); CLI in `tools/wargame_cli.py`.
- **In-game UI verification**: `tools/qa_e2e.py` runs a 7-case matrix (HUD/PANEL with and without layout, tab switch, resize recalibration, exe self-check); 7/7 PASS on this machine; report `docs/QA_E2E.md`.
- **ML feasibility**: `tools/train_save_model.py` trains and saves `models/recog_27px.pt` (40-epoch default: within 0.662 / LOBO 0.503; 0.734 / 0.641 at 60 epochs); inference `clashlab/recog_model.py`; report `docs/ML_FEASIBILITY.md`.
- New corner-labeling tool `tools/label_corners/` for auto-calibration data.

## What it does

- **Overlay**: a read-only, click-through HUD plus a four-page PANEL (research / layout / collect / settings), docked next to the emulator client area.
- **Calibration**: 44×44 DLT homography, with automatic recalibration when the client area changes size by more than 10%.
- **Scoring**: seven weighted metrics collapse into a 0–100 score, an S–F grade and weak points with a direction.
- **Tactics**: findings feed the brief, the LLM prompt and the panel; there is a giant-arrow (Queen Walk) tactical diagram; 2D simulation candidate drop points are supported.
- **2D**: `layout.json` becomes a top-down PNG and a 2D interchange JSON, ready for another 2D engine (`python -m clashlab.topdown_cli`).

## Install and run

You need Windows 10/11, Python 3.13 and LDPlayer 9 (client area 1280×720), plus numpy, opencv, pywin32, imgui_bundle and pillow.

```powershell
git clone https://github.com/Z1wind/clashlab-overlay.git
cd clashlab-overlay
python -m pip install -r requirements.txt
python run_overlay.py --show --mode HUD --always-on-top --run-seconds 8
python -m unittest discover -s tests   # all green
```

For the first run, start with 8 seconds and check the log. If `out/overlay/overlay.log` shows `target_rect=...`, `rect=(x,y,1280x720)`, `fps summary` and `runtime end`, then window discovery, calibration and rendering are all working. Modes, hotkeys, LLM setup and troubleshooting are covered in the [tutorial](docs/TUTORIAL_en.md).

## Commands

```powershell
# Pre-battle simulation: read a layout, simulate both sides
python -m clashlab.prebattle --layout bases\th16\03\layout.json --out out\prebattle

# Giant-arrow tactical diagram
python -m clashlab.overlay.giant_arrow_diagram --layout bases\th16\03\layout.json --out out\ga.png

# Build the exe
.\build_overlay.ps1

# Run the tests
python -m unittest discover -s tests
```

## Download

- [Release v0.1.0](https://github.com/Z1wind/clashlab-overlay/releases/tag/v0.1.0): `ClashOverlay.exe` (Windows x64, about 90 MB), source zip and `SHA256SUMS.txt`.

If you don't want to install Python, grab the exe. If you want to read or change the code, install from source.

## How the score works

| Metric | Weight | Status |
|---|---|---|
| Town Hall protection | 3 | available |
| Storage protection | 2 | available (N/A for defence-only layouts) |
| Air defence | 2 | available |
| Ground defence | 2 | available |
| Compartment quality | 2 | N/A, wall data incomplete |
| Wall efficiency | 1 | N/A, wall data incomplete |
| Entry control | 1 | available |

The seven weights add up to 13 and are rescaled to 0–100, then graded S≥90, A≥80, B≥70, C≥55, D≥40. Compartment and wall metrics stay N/A until automatic wall extraction passes; the other five are usable today.

## How it works

```text
LDPlayer 1280x720 --PrintWindow--> frame + 44x44 homography
        --> score / weak points / ring / simulation --> ImGui overlay + PNG
```

Capture and calibration live in `clashlab/vision.py` and `clashlab/geo.py` (the single entry point for coordinate conversion). Scoring and weak-point attribution read the size and stat tables in `assets.py`. The tactics layer turns the findings into a brief for the rule engine or an LLM, and the result is drawn in the overlay or exported as PNG / JSON.

## Known limitations

- **Building recognition is not usable yet**: same-tier accuracy at 27 px/tile is 0.523. Manual labels on the high-zoom tier were audited and at least 42% turned out to be wrong, so the seemingly higher numbers cannot be trusted and there is no usable detection build.
- **Automatic wall extraction did not pass**, so compartment quality and wall efficiency show N/A.
- **The vision LLM only handles OCR well**: resource numbers 4/4, building classification 3/16.
- **Verified only on Windows + LDPlayer at 1280×720**; other emulators and resolutions are untested.

## Community

This is basically a one-person project right now, and contributions are very welcome. Any of the following is useful:

- **Base annotations**: TH16 base layouts marked on the 44×44 grid (other Town Hall levels are welcome too). Put them under `bases/<TH>/<layout>/` with the original screenshot and a one-line note; if you also marked walls, say where the data came from.
- **Layout JSON**: a `layout.json` or 2D interchange JSON. Several independent versions of the same base are especially useful.
- **Recognition samples**: clean scouting frames paired with their layout, at both the 27 px and 70 px tiers. Recognition is the weakest part of the project, so samples are worth more than code right now.
- **Algorithm work**: scoring metrics, weak-point attribution, 2D simulation, overlay performance and interaction — any of it.

How to submit:

- **Issues**: use the `Bug report` template for bugs (include the command, the tail of `out/overlay/overlay.log` and your environment) and `Feature request` for ideas, picking the relevant area (overlay / recognition / layout score / tactics / docs-tooling).
- **Pull requests**: follow `.github/PULL_REQUEST_TEMPLATE.md` and describe what changed and how you verified it. For data, note the source (your own capture or public community data) and keep local paths and keys out. Run `python -m unittest discover -s tests` before changing code.

The full ground rules are in [CONTRIBUTING.md](CONTRIBUTING.md). Even an issue describing the kind of base analysis you want, or passing the repo on to someone who needs it, is a real help.

## Privacy

No injection into LDPlayer, no memory reading, no game-server access. No keys are shipped (LLM credentials come from local config or environment variables). Apart from LLM calls you enable yourself, screenshots and layout data stay on your machine and are not uploaded.

## Acknowledgements

The full list of borrowed work, authors and licences is in **[ATTRIBUTIONS.md](ATTRIBUTIONS.md)**. Main credits:

- [@koniz-dev](https://github.com/koniz-dev) · [clash-blueprint-engine](https://github.com/koniz-dev/clash-blueprint-engine): the seven defence metrics and weak-point system
- [@Peter537](https://github.com/Peter537) · [clash-of-clans-base-validator](https://github.com/Peter537/clash-of-clans-base-validator): geometry validation and building size tables
- [@ClashKingInc](https://github.com/ClashKingInc/ClashKingAssets), [@chiefpansancolt](https://github.com/chiefpansancolt), [@Statscell](https://github.com/Statscell): asset and data references
- [FICTURE7/CoCSharp](https://github.com/FICTURE7/CoCSharp), [DFanso/coc-attack-bot](https://github.com/DFanso/coc-attack-bot): read but not adopted, still shaped design decisions

## License

MIT, see [LICENSE](LICENSE). Third-party attribution is collected in ATTRIBUTIONS; game assets belong to Supercell and follow the Supercell Fan Content Policy.

For learning and research only. Follow Supercell's Terms of Service; use at your own risk.
