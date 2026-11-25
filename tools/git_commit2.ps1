$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: reposition as LLM-assisted layout research tool, add ATTRIBUTIONS, screenshots, license'
& $g log --oneline -3
$n = (& $g ls-files | Measure-Object -Line).Lines
Write-Output ('tracked files: ' + $n)
$m = Get-ChildItem '.git' -Recurse -File | Measure-Object Length -Sum
Write-Output ('git dir MB: ' + [math]::Round($m.Sum/1MB,1))
