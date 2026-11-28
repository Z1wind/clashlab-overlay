& 'D:/Python313/python.exe' -u 'tools/worklog_v21.py'
& 'D:/Python313/python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:/Temp/mingit2/cmd/git.exe'
& $g -C . add -A
& $g -C . commit -m 'docs: v2.1 18-base retrain + release notes; CV partial results' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:/Python313/python.exe' -u 'tools/push_changes.py' *> 'out/logs/push_v21_docs.log'
Write-Output ('push_exit=' + $LASTEXITCODE)