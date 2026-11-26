$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'fix(annotate): move calibration hint bar above canvas (was covering top corners) + larger corner hit radius'
& $g log --oneline -1
