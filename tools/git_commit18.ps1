$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Copy-Item 'out\qa_e2e\panel_strategy_crop.png' 'docs\screenshots\panel_strategy.png' -Force
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: add panel strategy-line screenshot'
& $g log --oneline -1
