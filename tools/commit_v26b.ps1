& 'D:\Python313\python.exe' -u 'tools/update_doc_v26.py'
& 'D:\Python313\python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'fix(apk): v0.2.6 margin 15% so image stays ~77% of screen; rebuild' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v26b.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_v26b.log' -Tail 4 | Out-String -Width 120