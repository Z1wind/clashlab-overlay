$g = 'E:\Temp\mingit2\cmd\git.exe'
Add-Content -Path '.gitignore' -Value 'dist_exe/'
Add-Content -Path '.gitignore' -Value 'build_exe/'
Add-Content -Path '.gitignore' -Value 'android/build_ci/'
Add-Content -Path '.gitignore' -Value '*.pkg'
Add-Content -Path '.gitignore' -Value '*.pyz'
& $g rm -r --cached 'dist_exe' 'build_exe' 'android/build_ci' 2>&1 | Select-Object -Last 2
& $g add -A
& $g commit --amend -m 'feat(desktop): v1.3 auto-preannotation (ONNX gate+type inside EXE); models + docs; smoke n=72/4.2s' 2>&1 | Select-Object -Last 2
& $g ls-files | Select-String -Pattern 'dist_exe|build_exe|\.pkg$' | Measure-Object | ForEach-Object { Write-Output ('tracked_big_left=' + $_.Count) }
$env:GH_TOKEN='GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_v13b.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_v13b.log' -Tail 4 | Out-String -Width 120