Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$exe = (Get-Item 'dist_exe\ClashLabAnnotator.exe').FullName
$p = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
Start-Sleep -Seconds 14
Write-Output '--- processes ---'
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 110
Write-Output '--- any error window ---'
Get-Process | Where-Object { $_.MainWindowTitle -like '*exception*' -or $_.MainWindowTitle -like '*错误*' } | Select-Object Id,ProcessName,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 110
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue