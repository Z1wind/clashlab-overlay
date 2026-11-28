& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit --amend -m 'feat(ml): train on user 8 real annotations - 6 good bases CV top1 88.2%/top3 94.8%; b01/b02 diagnosed mislabeled' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_train2.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_train2.log' -Tail 4 | Out-String -Width 120