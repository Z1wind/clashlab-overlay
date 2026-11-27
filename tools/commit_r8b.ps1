& 'D:\Python313\python.exe' -u 'tools\docs_cv_r8.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'test(ml): multi-base leave-one-out CV smoke (mean top1 7.7% on legacy misaligned annotations); docs' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_r8b.log'
Write-Output ('push_exit=' + $LASTEXITCODE)