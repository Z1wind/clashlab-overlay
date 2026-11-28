& 'D:/Python313/python.exe' -u 'tools/worklog_cv18.py'
& 'D:/Python313/python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:/Temp/mingit2/cmd/git.exe'
& $g -C . add -A
& $g -C . commit -m 'docs: 18-fold CV anomaly + 8-fold subset fallback; data coverage analysis' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:/Python313/python.exe' -u 'tools/push_changes.py' *> 'out/logs/push_cv18doc.log'
Write-Output ('push_exit=' + $LASTEXITCODE)