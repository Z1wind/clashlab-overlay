& 'D:/Python313/python.exe' -u 'tools/worklog_round11.py'
& 'D:/Python313/python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:/Temp/mingit2/cmd/git.exe'
& $g -C . add -A
& $g -C . commit -m 'feat(ml): per-type error analysis (small collectors weakest), release_from_labels one-command pipeline; docs' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:/Python313/python.exe' -u 'tools/push_changes.py' *> 'out/logs/push_round11.log'
Write-Output ('push_exit=' + $LASTEXITCODE)