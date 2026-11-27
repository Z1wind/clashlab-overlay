& 'D:\Python313\python.exe' -u 'tools\package_v29.py'
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
$src = 'tools\upload_v28.py'
$dst = 'tools\upload_v29.py'
(Get-Content $src -Raw -Encoding UTF8).Replace('v0.2.8','v0.2.9') | Set-Content $dst -Encoding UTF8
& 'D:\Python313\python.exe' -u 'tools\upload_v29.py' 2>&1 | Select-Object -Last 5
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(apk): v0.2.9 overall progress (done N/20); device QA 0->1->next page' 2>&1 | Select-Object -Last 2
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v29.log'
Write-Output ('push_exit=' + $LASTEXITCODE)