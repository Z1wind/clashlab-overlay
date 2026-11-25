$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(2d): layout -> top-down PNG + 2D interchange JSON (CLI, tests, docs)'
& $g log --oneline -1
