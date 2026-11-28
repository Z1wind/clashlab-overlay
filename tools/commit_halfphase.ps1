& 'D:\Python313\python.exe' -u 'tools\worklog_halfphase.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'test(ml): half-phase candidate merging - higher precision/type, lower recall; phases param added; docs' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_halfphase.log'
Write-Output ('push_exit=' + $LASTEXITCODE)