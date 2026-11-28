& 'D:\Python313\python.exe' -u 'tools\worklog_gridseg.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'test(ml): grid-seg detector prototype fails with 8 bases (recall .10); docs' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_gridseg.log'
Write-Output ('push_exit=' + $LASTEXITCODE)