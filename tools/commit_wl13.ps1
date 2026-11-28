& 'D:\Python313\python.exe' -u 'tools\worklog_v13.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: worklog training + v1.3 preannotation delivery' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_wl13.log'
Write-Output ('push_exit=' + $LASTEXITCODE)