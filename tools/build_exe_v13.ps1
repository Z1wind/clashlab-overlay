$ErrorActionPreference='Continue'
$root = (Get-Location).Path
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Remove-Item 'dist_exe\ClashLabAnnotator.exe' -Force -ErrorAction SilentlyContinue
$html = Join-Path $root 'dist\ClashLabAnnotator_Desktop_v3.html'
$img = Join-Path $root 'android\assets\img'
$models = Join-Path $root 'models'
$main = Join-Path $root 'tools\desktop_app.py'
$args = @(
 '--noconfirm','--onefile','--windowed','--name','ClashLabAnnotator',
 '--add-data',($html + ';.'),
 '--add-data',($img + ';img'),
 '--add-data',((Join-Path $models 'pipeline_gate.onnx') + ';models'),
 '--add-data',((Join-Path $models 'pipeline_type.onnx') + ';models'),
 '--add-data',((Join-Path $models 'pipeline_types.json') + ';models'),
 '--collect-all','webview','--collect-all','clr_loader','--collect-all','pythonnet',
 '--collect-all','onnxruntime',
 '--hidden-import','clr','--hidden-import','webview.platforms.edgechromium',
 '--hidden-import','tools.preannotate_core','--hidden-import','clashlab.geo','--hidden-import','clashlab.assets',
 '--distpath',(Join-Path $root 'dist_exe'),
 '--workpath',(Join-Path $root 'build_exe'),
 $main
)
& 'D:\Python313\python.exe' -m PyInstaller @args *> 'out\logs\pyinstaller_v13.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pyinstaller_v13.log' -Tail 4 | Out-String -Width 160
Get-ChildItem 'dist_exe\*.exe' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ($_.Name + " " + $_.Length) }