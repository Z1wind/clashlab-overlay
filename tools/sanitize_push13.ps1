& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit --amend -m 'feat(desktop): v1.3 auto-preannotation (ONNX gate+type inside EXE); models + docs; smoke n=72/4.2s' 2>&1 | Select-Object -Last 1
& $g grep -n 'ghp_' HEAD -- . 2>&1 | Select-Object -First 3
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v13c.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_v13c.log' -Tail 4 | Out-String -Width 120