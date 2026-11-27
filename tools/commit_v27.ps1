& 'D:\Python313\python.exe' -u 'tools\package_v27.py'
& 'D:\Python313\python.exe' -u 'tools\sanitize_tokens.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(apk): v0.2.7 edge auto-pan so corners reach arbitrarily far outside image; help text update' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v27.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-ChildItem 'dist\ClashLabAnnotator_20bases_v0.2.7.apk' | ForEach-Object { Write-Output ($_.Length.ToString() + " bytes md5 " + (Get-FileHash $_.FullName -Algorithm MD5).Hash) }