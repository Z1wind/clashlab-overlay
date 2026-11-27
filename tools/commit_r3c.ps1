& 'D:\Python313\python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'verify: CI artifact APK (20 imgs, annotate6 md5 match) + release v0.3.7 asset md5 check' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_r3c.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_r3c.log' -Tail 5 | Out-String -Width 130