& 'D:/Python313/python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:/Temp/mingit2/cmd/git.exe'
& $g -C . add -A
& $g -C . commit -m 'feat(ml): retrain on 18 labeled bases (v2.1); b03 P91.8/R85.7; release EXE + scripts' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:/Python313/python.exe' -u 'tools/push_changes.py' *> 'out/logs/push_v21.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out/logs/push_v21.log' -Tail 4 | Out-String -Width 140