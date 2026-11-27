$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: overnight r3 worklog + morning brief' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_r3.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_r3.log' -Tail 5 | Out-String -Width 130