$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(levels): building/troop/hero levels in wargame + set_levels CLI + LEVELS.md (measured 18.95%->8.55%)'
& $g log --oneline -1
