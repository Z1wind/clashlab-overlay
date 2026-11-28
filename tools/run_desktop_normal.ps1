$env:CLASHLAB_SMOKE=''
$p = Start-Process -FilePath 'D:\Python313\python.exe' -ArgumentList '-u','tools\desktop_app.py' -WorkingDirectory (Get-Location) -PassThru -RedirectStandardOutput 'out\logs\desk_normal.log' -RedirectStandardError 'out\logs\desk_normal_err.log'
Start-Sleep -Seconds 12
Get-Process -Id $p.Id -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle | Format-Table -AutoSize | Out-String -Width 100
Get-ChildItem -Path . -Filter '*.log' -Recurse -ErrorAction SilentlyContinue | Out-Null
Write-Output '--- stderr ---'
Get-Content 'out\logs\desk_normal_err.log' -Tail 20 -ErrorAction SilentlyContinue | Out-String -Width 200
Write-Output '--- stdout ---'
Get-Content 'out\logs\desk_normal.log' -Tail 10 -ErrorAction SilentlyContinue | Out-String -Width 200
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue