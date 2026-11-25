$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$g = Join-Path $env:TEMP 'gitportable\mingit\cmd\git.exe'
if (-not (Test-Path $g)) { throw 'portable git missing' }
if (Test-Path '.git') { Remove-Item '.git' -Recurse -Force }
& $g init -b main
& $g config user.name 'ClashLab'
& $g config user.email 'noreply@clashlab.local'
& $g add -A
& $g commit -m 'chore: initial open-source release v0.1.0'
& $g log --oneline -1
$n = (& $g ls-files | Measure-Object -Line).Lines
Write-Output ('tracked files: ' + $n)
& $g ls-files | ForEach-Object { ($_ -split '/')[0] } | Group-Object | Sort-Object Count -Descending | Select-Object -First 10 Name,Count | Format-Table -AutoSize | Out-String -Width 50
$m = Get-ChildItem '.git' -Recurse -File | Measure-Object Length -Sum
Write-Output ('git dir MB: ' + [math]::Round($m.Sum/1MB,1))
Write-Output ('out/dist tracked: ' + ((& $g ls-files | Select-String '^(out/|dist/|build_v|scripts/)' | Measure-Object).Count))
