$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(levels): TH16 max-level fill for 6 annotated bases + ruleset max_level_of + experimental color estimator'
& $g log --oneline -1
