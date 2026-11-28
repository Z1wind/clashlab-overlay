$labels = @()
$labels += (Join-Path $env:USERPROFILE 'Downloads\annot_b01 (1).json')
$labels += (Join-Path $env:USERPROFILE 'Downloads\annot_b02 (1).json')
for ($i=3; $i -le 8; $i++) { $labels += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
foreach ($n in @('b10','b11','b12','b14','b15','b16','b17','b18','b19','b20')) { $labels += (Join-Path $env:USERPROFILE ('Downloads\annot_' + $n + '.json')) }
Write-Output ('total=' + $labels.Count)
& 'D:/Python313/python.exe' -u 'tools/patch_cv_env.py'
$env:CLASHLAB_EXPORTS = ($labels -join [char]10)
& 'D:/Python313/python.exe' -u 'tools/train_hybrid_cv.py' *> 'out/logs/hybrid18_cv.log'
Write-Output ('cv_exit=' + $LASTEXITCODE)
Remove-Item Env:/CLASHLAB_EXPORTS
Get-Content 'out/logs/hybrid18_cv.log' -Tail 6 | Out-String -Width 170