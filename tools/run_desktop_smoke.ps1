$env:CLASHLAB_SMOKE='1'
$p = Start-Process -FilePath 'D:\Python313\python.exe' -ArgumentList '-u','tools\desktop_app.py' -WorkingDirectory (Get-Location) -PassThru -RedirectStandardOutput 'out\logs\desktop_smoke.log' -RedirectStandardError 'out\logs\desktop_smoke_err.log'
$null = $p.WaitForExit(60000)
Write-Output ('exit=' + $p.ExitCode)
Get-Content 'out\logs\desktop_smoke.log' -Tail 5 -ErrorAction SilentlyContinue | Out-String -Width 200
Get-Content 'out\logs\desktop_smoke_err.log' -Tail 5 -ErrorAction SilentlyContinue | Out-String -Width 200
Get-ChildItem 'tools\smoke_result.json' -ErrorAction SilentlyContinue | ForEach-Object { Get-Content $_.FullName -Raw }
Get-ChildItem "$env:USERPROFILE\Downloads\ClashLab标注" -ErrorAction SilentlyContinue | Select-Object Name,Length | Format-Table -AutoSize | Out-String -Width 80