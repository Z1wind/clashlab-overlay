$ErrorActionPreference = 'Continue'
$g = 'E:\Temp\mingit2\cmd\git.exe'
Write-Output '--- tracked img files ---'
$tracked = & $g ls-files 'android/assets/img'
Write-Output ('tracked: ' + $tracked.Count)
& $g check-ignore -v 'android/assets/img/b01.jpg' 2>&1
Write-Output '--- add ---'
& $g add -f 'android/assets/img'
& $g status --short 'android/assets/img' | Select-Object -First 3
& $g commit -m 'assets: add 20 TH16 base images to repo so CI-built APK includes them' 2>&1 | Select-Object -Last 2
$env:GH_TOKEN = 'GH_TOKEN_PLACEHOLDER'
& 'D:\Python313\python.exe' -u 'tools\push_changes.py' *> 'out\logs\push_imgs.log'
Write-Output ('push_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\push_imgs.log' -Tail 6 | Out-String -Width 140