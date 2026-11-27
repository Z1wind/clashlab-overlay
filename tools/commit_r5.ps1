& 'D:\Python313\python.exe' -u 'tools\worklog_r45.py'
& 'D:\Python313\python.exe' -m unittest discover -s tests 2>&1 | Select-String -Pattern 'Ran |^OK|FAILED' | ForEach-Object { $_.Line }
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'test+docs: outside-corner corners_norm supported by dataset converter; round 4-5 worklog' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_r5.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_r5.log' -Tail 4 | Out-String -Width 120