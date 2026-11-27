& 'D:\Python313\python.exe' -u 'tools\package_v30.py'
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
$src = 'tools\upload_v29.py'
$dst = 'tools\upload_v30.py'
(Get-Content $src -Raw -Encoding UTF8).Replace('v0.2.9','v0.3.0') | Set-Content $dst -Encoding UTF8
& 'D:\Python313\python.exe' -u 'tools\upload_v30.py' 2>&1 | Select-Object -Last 5
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(apk): v0.3.0 drag placed building to adjust tile; headless selftest 18,18 -> 23,22' 2>&1 | Select-Object -Last 2
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v30.log'
Write-Output ('push_exit=' + $LASTEXITCODE)