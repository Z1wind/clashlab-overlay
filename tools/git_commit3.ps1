$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path 'docs\qa' | Out-Null
Copy-Item 'out\qa\soak_report.md' 'docs\qa\soak_report.md' -Force
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'test: add 2-round real-machine soak report (7/7 both rounds)'
& $g log --oneline -3
$n = (& $g ls-files | Measure-Object -Line).Lines
Write-Output ('tracked files: ' + $n)
