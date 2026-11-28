& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(ml): hybrid preannotation (gate + ArcFace embedding NN) F1 .658/R71/type92; v1.5 EXE; 8-base retrain' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v15.log'
Write-Output ('push_exit=' + $LASTEXITCODE)