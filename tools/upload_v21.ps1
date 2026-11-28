& 'D:/Python313/python.exe' -u 'tools/package_v21.py'
Copy-Item 'tools/upload_exe20.py' 'tools/upload_exe21.py' -Force
& 'D:/Python313/python.exe' -c "p='tools/upload_exe21.py'; t=open(p,encoding='utf-8').read().replace('Desktop_v2.0.exe','Desktop_v2.1.exe'); open(p,'w',encoding='utf-8',newline='\n').write(t)"
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
for ($i=0; $i -lt 3; $i++) {
  & 'D:/Python313/python.exe' -u 'tools/upload_exe21.py' *> 'out/logs/upload21.log'
  if ($LASTEXITCODE -eq 0) { break }
  Start-Sleep -Seconds 3
}
Write-Output ('upload_exit=' + $LASTEXITCODE)
Get-Content 'out/logs/upload21.log' -Tail 5 | Out-String -Width 140