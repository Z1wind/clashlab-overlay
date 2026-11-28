$exe = (Get-Item 'dist_exe\ClashLabAnnotator.exe').FullName
Remove-Item 'dist_exe\smoke_result.json' -Force -ErrorAction SilentlyContinue
Get-ChildItem "$env:USERPROFILE\Downloads\ClashLab标注" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
$oldPath=$env:PATH
$env:PATH='C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem'
$env:CLASHLAB_SMOKE='1'
$p = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
$null = $p.WaitForExit(90000)
$env:PATH=$oldPath; Remove-Item Env:\CLASHLAB_SMOKE
Write-Output ('nopython_exit=' + $p.ExitCode)
if (Test-Path 'dist_exe\smoke_result.json') { Get-Content 'dist_exe\smoke_result.json' -Raw } else { Write-Output 'NO_SMOKE' }
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$p2 = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
Start-Sleep -Seconds 12
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle } | Select-Object Id,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 110
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue