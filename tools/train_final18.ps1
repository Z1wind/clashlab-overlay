$labels = @()
$labels += (Join-Path $env:USERPROFILE 'Downloads\annot_b01 (1).json')
$labels += (Join-Path $env:USERPROFILE 'Downloads\annot_b02 (1).json')
for ($i=3; $i -le 8; $i++) { $labels += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
foreach ($n in @('b10','b11','b12','b14','b15','b16','b17','b18','b19','b20')) { $labels += (Join-Path $env:USERPROFILE ('Downloads\annot_' + $n + '.json')) }
$bak = 'models/_good_v20'
if (Test-Path $bak) { Remove-Item $bak -Recurse -Force }
New-Item -ItemType Directory -Path $bak | Out-Null
Copy-Item 'models/hybrid_*' $bak
$env:CLASHLAB_EXPORTS = ($labels -join [char]10)
& 'D:/Python313/python.exe' -u 'tools/train_hybrid_final.py' *> 'out/logs/final18_train.log'
Write-Output ('train_exit=' + $LASTEXITCODE)
Remove-Item Env:/CLASHLAB_EXPORTS
Get-Content 'out/logs/final18_train.log' -Tail 4 | Out-String -Width 140
& 'D:/Python313/python.exe' -u 'tools/export_hybrid_onnx.py' 2>$null | Select-String -Pattern 'diff' | ForEach-Object { $_.Line }
& 'D:/Python313/python.exe' -u 'tools/retest_preannotate.py' 2>&1 | Select-Object -Last 4 | Out-String -Width 150