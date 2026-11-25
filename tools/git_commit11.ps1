$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat: annotation tool, wall symmetry, recog dataset, base-link analysis, docs copy'
& $g log --oneline -1
$n = (& $g ls-files | Measure-Object -Line).Lines
Write-Output ('tracked: ' + $n)
