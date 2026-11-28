& 'D:/Python313/python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:/Temp/mingit2/cmd/git.exe'
& $g -C . add -A
& $g -C . commit -m 'feat(desktop): v2.0 supplement preannotation (keep existing, add missing only); proxy-bypass fallback for API push/upload' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:/Python313/python.exe' -u 'tools/push_changes.py' *> 'out/logs/push_v20.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out/logs/push_v20.log' -Tail 4 | Out-String -Width 140