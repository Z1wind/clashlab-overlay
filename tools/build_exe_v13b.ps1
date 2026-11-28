$ErrorActionPreference='Continue'
& 'D:\Python313\python.exe' -u 'tools\fix_smoke_mode.py'
& 'D:\Python313\python.exe' -m py_compile 'tools\desktop_app.py' 'tools\preannotate_core.py'
Write-Output ('compile_exit=' + $LASTEXITCODE)
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Remove-Item 'dist_exe\ClashLabAnnotator.exe' -Force -ErrorAction SilentlyContinue
$root = (Get-Location).Path
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
 '--hidden-import','onnxruntime',
 '--hidden-import','clr','--hidden-import','webview.platforms.edgechromium',
 '--hidden-import','tools.preannotate_core','--hidden-import','clashlab.geo','--hidden-import','clashlab.assets',
 '--exclude-module','torch','--exclude-module','torchvision','--exclude-module','onnx','--exclude-module','onnxscript','--exclude-module','triton',
 '--distpath',(Join-Path $root 'dist_exe'),
 '--workpath',(Join-Path $root 'build_exe'),
 $main
)
& 'D:\Python313\python.exe' -m PyInstaller @args *> 'out\logs\pyinstaller_v13b.log'
Write-Output ('exit=' + $LASTEXITCODE)
Get-Content 'out\logs\pyinstaller_v13b.log' -Tail 3 | Out-String -Width 160
Get-ChildItem 'dist_exe\*.exe' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ($_.Name + " " + $_.Length) }