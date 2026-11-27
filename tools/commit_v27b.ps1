& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'docs: APK_20BASES v0.2.7 (edge auto-pan) + upload script' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v27b.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_v27b.log' -Tail 3 | Out-String -Width 120