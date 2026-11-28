$exe = (Get-Item 'dist_exe\ClashLabAnnotator.exe').FullName
Remove-Item 'dist_exe\smoke_result.json' -Force -ErrorAction SilentlyContinue
Get-ChildItem "$env:USERPROFILE\Downloads\ClashLab标注" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
# 去掉 PATH 中的 Python，模拟“无 Python 环境”
$oldPath = $env:PATH
$env:PATH = 'C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem'
$env:CLASHLAB_SMOKE='1'
$p = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
$null = $p.WaitForExit(90000)
$env:PATH = $oldPath
Remove-Item Env:\CLASHLAB_SMOKE
Write-Output ('exit=' + $p.ExitCode)
$sr = 'dist_exe\smoke_result.json'
if (Test-Path $sr) { Get-Content $sr -Raw; Write-Output 'SMOKE_FILE_OK' } else { Write-Output 'SMOKE_FILE_MISSING' }
Get-ChildItem "$env:USERPROFILE\Downloads\ClashLab标注" -ErrorAction SilentlyContinue | Select-Object Name,Length | Format-Table -AutoSize | Out-String -Width 80
# 窗口标题（正常启动）
$p2 = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
Start-Sleep -Seconds 10
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 110
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue