$exe = (Get-Item 'dist_exe\ClashLabAnnotator.exe').FullName
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Remove-Item 'dist_exe\smoke2_result.json' -Force -ErrorAction SilentlyContinue
$env:CLASHLAB_SMOKE='2'
$p = Start-Process -FilePath $exe -WorkingDirectory (Get-Location) -PassThru
$null = $p.WaitForExit(180000)
Remove-Item Env:\CLASHLAB_SMOKE
Write-Output ('smoke2_exit=' + $p.ExitCode)
if (Test-Path 'dist_exe\smoke2_result.json') { Get-Content 'dist_exe\smoke2_result.json' -Raw } else { Write-Output 'NO_SMOKE2' }
Remove-Item 'dist_exe\smoke_result.json' -Force -ErrorAction SilentlyContinue
$env:CLASHLAB_SMOKE='1'
$p2 = Start-Process -FilePath $exe -WorkingDirectory (Get-Location) -PassThru
$null = $p2.WaitForExit(120000)
Remove-Item Env:\CLASHLAB_SMOKE
Write-Output ('smoke1_exit=' + $p2.ExitCode)
if (Test-Path 'dist_exe\smoke_result.json') { Get-Content 'dist_exe\smoke_result.json' -Raw } else { Write-Output 'NO_SMOKE1' }