& 'D:\Python313\python.exe' -u 'tools\package_v13.py'
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
$src='tools\upload_exe12.py'
$dst='tools\upload_exe13.py'
(Get-Content $src -Raw -Encoding UTF8).Replace('Desktop_v1.2.exe','Desktop_v1.3.exe') | Set-Content $dst -Encoding UTF8
& 'D:\Python313\python.exe' -u 'tools\upload_exe13.py' *> 'out\logs\upload13.log'
Write-Output ('upload_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\upload13.log' -Tail 5 | Out-String -Width 140