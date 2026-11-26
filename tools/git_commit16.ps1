$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat: TH1-19 data, strategy recommender, spawn line/region optimizer (+17.9->24.7%), quad model'
& $g log --oneline -1
