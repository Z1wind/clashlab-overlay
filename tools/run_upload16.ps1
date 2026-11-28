& 'D:\Python313\python.exe' -u 'tools\mk_upload16.py'
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\upload_exe16.py' *> 'out\logs\upload16.log'
Write-Output ('upload_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\upload16.log' -Tail 4 | Out-String -Width 140