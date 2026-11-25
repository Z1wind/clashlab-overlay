$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: trim comments and add bilingual README/tutorial/attributions'
& $g log --oneline -2
$n = (& $g ls-files | Measure-Object -Line).Lines
Write-Output ('tracked: ' + $n)
