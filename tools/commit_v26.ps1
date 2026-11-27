& 'D:\Python313\python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(apk): v0.2.6 corners can be dragged outside the image (18% canvas margin); selftest via headless browser' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v26.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_v26.log' -Tail 5 | Out-String -Width 130