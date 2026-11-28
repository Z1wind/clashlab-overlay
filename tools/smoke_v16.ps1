Get-ChildItem 'dist_exe\ClashLabAnnotator.exe' | ForEach-Object { Write-Output ($_.Length.ToString() + " bytes") }
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Remove-Item 'dist_exe\smoke2_result.json' -Force -ErrorAction SilentlyContinue
$env:CLASHLAB_SMOKE='2'
$p = Start-Process -FilePath (Get-Item 'dist_exe\ClashLabAnnotator.exe').FullName -WorkingDirectory (Get-Location) -PassThru
$null = $p.WaitForExit(240000)
Remove-Item Env:\CLASHLAB_SMOKE
Write-Output ('smoke2_exit=' + $p.ExitCode)
if (Test-Path 'dist_exe\smoke2_result.json') { Get-Content 'dist_exe\smoke2_result.json' -Raw } else { Write-Output 'NO_SMOKE2' }