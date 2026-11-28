$files = @()
$files += (Join-Path $env:USERPROFILE 'Downloads\annot_b01 (1).json')
$files += (Join-Path $env:USERPROFILE 'Downloads\annot_b02 (1).json')
for ($i=3; $i -le 8; $i++) { $files += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
$exp = ($files -join ',')
Write-Output '=== classifier 8 bases ==='
& 'D:\Python313\python.exe' -u 'tools/train_real_aug.py' --export $exp --epochs 40 --size 112 --out 'models\apk_type_cls8.pt' --report 'out\apk_type_report8.json' *> 'out\logs\cls8.log'
Write-Output ('cls_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\cls8.log' | Select-String -Pattern 'total|hold|CV mean|saved' | ForEach-Object { $_.Line }
Write-Output '=== pipeline 8 bases ==='
& 'D:\Python313\python.exe' -u 'tools/train_pipeline_cv.py' --export $exp *> 'out\logs\pipeline8.log'
Write-Output ('pipe_exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pipeline8.log' | Select-String -Pattern 'bases|hold|PIPELINE MEAN' | ForEach-Object { $_.Line }