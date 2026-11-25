$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat: CI badge, --version, Chinese window title, issue/PR templates, CoC'
& $g log --oneline -1
$n = (& $g ls-files | Measure-Object -Line).Lines
Write-Output ('tracked: ' + $n)
