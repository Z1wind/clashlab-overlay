& 'D:\Python313\python.exe' -u 'tools\package_v28.py'
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
$src = 'tools\upload_v27.py'
$dst = 'tools\upload_v28.py'
(Get-Content $src -Raw -Encoding UTF8).Replace('v0.2.7','v0.2.8') | Set-Content $dst -Encoding UTF8
& 'D:\Python313\python.exe' -u 'tools\upload_v28.py' 2>&1 | Select-Object -Last 5
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(apk): v0.2.8 auto-jump to next uncalibrated image after export; device QA 1/20 -> 2/20' 2>&1 | Select-Object -Last 2
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v28.log'
Write-Output ('push_exit=' + $LASTEXITCODE)