$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\upload_v27.py' 2>&1 | Select-Object -Last 5
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'fix(apk): v0.2.7 autopan STEP=2 with pan cap; device QA MIN_Y=-0.6' 2>&1 | Select-Object -Last 2
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v27c.log'
Write-Output ('push_exit=' + $LASTEXITCODE)