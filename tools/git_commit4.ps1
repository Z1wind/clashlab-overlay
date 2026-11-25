$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: fix borrowed-repo links (chiefpansancolt/clash-of-clans-data, coc-auto-farm-ai)'
& $g log --oneline -4
