$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(visual): prettier HUD marks (glow/chips/brackets), panel gradient chrome, redesigned 2D top-down'
& $g log --oneline -1
