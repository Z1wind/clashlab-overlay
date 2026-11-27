& 'D:\Python313\python.exe' -u 'tools\docs_r68.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(ml): one-command train_from_apk_export pipeline + smoke test; docs r6-8 + morning brief' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_r8.log'
Write-Output ('push_exit=' + $LASTEXITCODE)