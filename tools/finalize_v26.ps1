$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools/replace_v26_asset.py' 2>&1 | Select-Object -Last 6
& 'D:\Python313\python.exe' -u 'tools/sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'fix(apk): v0.2.6 stage-relative 6% margin (image ~88%), corners reach 11 tiles horizontally; device QA HAS_OUTSIDE=true' 2>&1 | Select-Object -Last 2
& 'D:\Python313\python.exe' -u 'tools/push_changes.py' *> 'out\logs\push_v26c.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_v26c.log' -Tail 4 | Out-String -Width 120