& 'D:\Python313\python.exe' -u 'tools\package_v18.py'
Copy-Item 'tools\upload_exe17.py' 'tools\upload_exe18.py' -Force
& 'D:\Python313\python.exe' -c "p='tools/upload_exe18.py'; t=open(p,encoding='utf-8').read().replace('Desktop_v1.7.exe','Desktop_v1.8.exe'); open(p,'w',encoding='utf-8',newline='\n').write(t)"
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\upload_exe18.py' *> 'out\logs\upload18.log'
Write-Output ('upload_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\upload18.log' -Tail 4 | Out-String -Width 140