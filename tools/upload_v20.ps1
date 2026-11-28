& 'D:/Python313/python.exe' -u 'tools/package_v20.py'
Copy-Item 'tools/upload_exe19.py' 'tools/upload_exe20.py' -Force
& 'D:/Python313/python.exe' -c "p='tools/upload_exe20.py'; t=open(p,encoding='utf-8').read().replace('Desktop_v1.9.exe','Desktop_v2.0.exe'); open(p,'w',encoding='utf-8',newline='\n').write(t)"
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:/Python313/python.exe' -u 'tools/upload_exe20.py' *> 'out/logs/upload20.log'
Write-Output ('upload_exit=' + $LASTEXITCODE)
Get-Content 'out/logs/upload20.log' -Tail 4 | Out-String -Width 140