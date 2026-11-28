& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'fix: preannotation crop center offset (0.5 tile) caused low precision; v1.7 EXE (P0.90/R0.71 on b03)' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v17.log'
Write-Output ('push_exit=' + $LASTEXITCODE)