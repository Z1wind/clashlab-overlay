& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'chore: remove accidental PAT strings from scripts (secret scanning)' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_r3b.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_r3b.log' -Tail 6 | Out-String -Width 140