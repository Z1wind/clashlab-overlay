& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'fix(ml): retrain degradation incident - recover models from v1.7 exe, new train_hybrid_final (b03 P84/R87), v1.8 EXE' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v18.log'
Write-Output ('push_exit=' + $LASTEXITCODE)