& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(desktop): v1.3 auto-preannotation (ONNX gate+type inside EXE); models + docs; smoke n=72/4.2s' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v13.log'
Write-Output ('push_exit=' + $LASTEXITCODE)