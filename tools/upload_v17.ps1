& 'D:\Python313\python.exe' -u 'tools\package_v17.py'
Copy-Item 'tools\upload_exe16.py' 'tools\upload_exe17.py' -Force
& 'D:\Python313\python.exe' -c "p='tools/upload_exe17.py'; t=open(p,encoding='utf-8').read().replace('Desktop_v1.6.exe','Desktop_v1.7.exe'); open(p,'w',encoding='utf-8',newline='\n').write(t)"
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\upload_exe17.py' *> 'out\logs\upload17.log'
Write-Output ('upload_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\upload17.log' -Tail 4 | Out-String -Width 140