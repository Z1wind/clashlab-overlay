& 'D:\Python313\python.exe' -u 'tools\worklog_exp46.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'test(ml): ensemble/TTA, stronger aug, position refine - all negative results; docs' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_exp46.log'
Write-Output ('push_exit=' + $LASTEXITCODE)