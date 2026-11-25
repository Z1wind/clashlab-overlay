# Tutorial · from zero to running

> Windows 10/11 + LDPlayer 9 + Python 3.13. Chinese version: [教程.md](教程.md).

## 1. Install

```powershell
python -m pip install -r requirements.txt   # numpy/opencv/pywin32/imgui_bundle/pillow
```

## 2. Emulator

- Resolution **720×1280 / DPI 320**; landscape client becomes **1280×720**.
- On multi-monitor, the overlay refuses the primary display by design: move the emulator to the secondary screen or use `--allow-primary` temporarily.

## 3. First self-check

```powershell
python run_overlay.py --show --mode HUD --always-on-top --run-seconds 8
```

Expect `target_rect=...`, `rect=(x,y,1280x720)`, `fps summary`, `runtime end` in `out/overlay/overlay.log`.

## 4. Modes

| Mode | Command | Use |
|---|---|---|
| HUD | `--mode HUD` | annotations, click-through |
| PANEL | `--mode PANEL` | 440-px side panel, 4 pages |

Options: `--always-on-top`, `--run-seconds N`, `--allow-primary`.

## 5. What the panel shows

- **Research**: status `score 66.2 C`; two finding lines (TH bias / air coverage); `simulation: 23% predicted · best spawn (11,41)`; defence list drives HUD highlight.
- **Layout**: candidate canvas, run study, bottom score line.
- **Collect / Settings**: auto capture, hotkeys and parameters.

## 6. Reading the score

7 weighted metrics (total weight 13): TH 3 / storage 2 / air 2 / ground 2 / compartment 2 / walls 1 / entry 1. Grades: S≥90 A≥80 B≥70 C≥55 D≥40.

Compartment and wall metrics are N/A until wall data is completed; the other five are usable.

## 7. Layout data

The overlay reads `layouts/layout_current.json`; minimal form:

```json
{"name":"03","grid":44,"buildings":[{"type":"town-hall","tile":[17,28]}],"walls":[[12,20]]}
```

Quick try: `copy bases\th16\03\layout.json layouts\layout_current.json`.

## 8. LLM (optional)

The rule engine works offline. To enable an LLM: `provider_sources` in `~/.astrbot/data/cmd_config.json`, or env vars `CLASHLAB_BASE/CLASHLAB_KEY/CLASHLAB_MODEL`. No keys are shipped.

## 9. Commands

```powershell
python -m clashlab.prebattle --layout bases\th16\03\layout.json --out out\prebattle
python -m clashlab.overlay.giant_arrow_diagram --layout bases\th16\03\layout.json --out out\ga.png
.\build_overlay.ps1                    # build exe
python -m unittest discover -s tests    # 86 tests
```

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `target on primary display` | use secondary screen or `--allow-primary` |
| no score shown | missing `layouts/layout_current.json` |
| misaligned marks | resize auto-recalibrates; manual recalibration in settings |
| exits immediately | check `out/overlay/overlay.log` |
| missing CJK glyphs | install Microsoft YaHei |
