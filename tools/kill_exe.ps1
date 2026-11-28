Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 100
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Output ('remaining=' + ((Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Measure-Object).Count))
Remove-Item 'dist_exe\ClashLabAnnotator.exe' -Force -ErrorAction SilentlyContinue
Write-Output ('exe_exists=' + (Test-Path 'dist_exe\ClashLabAnnotator.exe'))