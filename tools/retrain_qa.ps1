$ErrorActionPreference='Stop'
& 'D:\Python313\python.exe' -u 'tools\patch_labels_args.py'
& 'D:\Python313\python.exe' -m py_compile 'tools\label_qa.py' 'tools\train_hybrid_full.py' 'tools\train_pipeline_full.py'
Write-Output ('compile=' + $LASTEXITCODE)
$labels = @()
$labels += (Join-Path $env:USERPROFILE 'Downloads\annot_b01 (1).json')
$labels += (Join-Path $env:USERPROFILE 'Downloads\annot_b02 (1).json')
for ($i=3; $i -le 8; $i++) { $labels += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
& 'D:\Python313\python.exe' -u 'tools\label_qa.py' --labels @labels | Tee-Object -FilePath 'out\logs\retrain_qa.log'
Write-Output ('qa_exit=' + $LASTEXITCODE)