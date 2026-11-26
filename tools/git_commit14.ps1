$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat: wargame sim, QA e2e matrix, ML checkpoint (within .630 / LOBO .477), docs for 2026-11-26'
& $g log --oneline -1
$n = (& $g ls-files | Measure-Object -Line).Lines
Write-Output ('tracked: ' + $n)
