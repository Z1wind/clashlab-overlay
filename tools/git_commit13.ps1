$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(annotate): grid calibration (drag 4 corners) + pointer mapping fix + /api/quad override'
& $g log --oneline -1
