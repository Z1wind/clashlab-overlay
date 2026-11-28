& 'D:/Python313/python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:/Temp/mingit2/cmd/git.exe'
& $g -C . add -A
& $g -C . commit -m 'docs: update RETRAIN.md for 18-base v2.1 baseline' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:/Python313/python.exe' -u 'tools/push_changes.py' *> 'out/logs/push_retrain_doc.log'
Write-Output ('push_exit=' + $LASTEXITCODE)