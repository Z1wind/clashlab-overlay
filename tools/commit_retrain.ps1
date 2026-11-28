& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(ml): one-command retrain pipeline (label QA -> hybrid train -> ONNX export) validated end-to-end; docs/RETRAIN.md' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_retrain.log'
Write-Output ('push_exit=' + $LASTEXITCODE)