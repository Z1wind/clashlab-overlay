& 'D:\Python313\python.exe' -u 'tools\worklog_v19eval.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'test(ml): v1.9 all-base consistency check (standard P81.5/R75.2, precise P86.5/type99.1); docs' 2>&1 | Select-Object -Last 1
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v19eval.log'
Write-Output ('push_exit=' + $LASTEXITCODE)