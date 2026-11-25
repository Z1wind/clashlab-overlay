$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: expand tutorial (troubleshooting, panel pages, scoring, LLM config, commands)'
& $g log --oneline -2
$n = (& $g ls-files | Measure-Object -Line).Lines
Write-Output ('tracked files: ' + $n)
