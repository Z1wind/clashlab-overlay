& 'D:\Python313\python.exe' -u 'tools\docs_r910.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: overnight rounds 9-10 + final morning brief (APK v0.3.0)' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_r910.log'
Write-Output ('push_exit=' + $LASTEXITCODE)