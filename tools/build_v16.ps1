& 'D:\Python313\python.exe' -u 'tools\patch_smoke_modes.py'
& 'D:\Python313\python.exe' -m py_compile 'tools\desktop_app.py'
Write-Output ('compile=' + $LASTEXITCODE)
# 构建 v1.6
$ErrorActionPreference='Continue'
$root = (Get-Location).Path
Get-Process ClashLabAnnotator -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Remove-Item 'dist_exe\ClashLabAnnotator.exe' -Force -ErrorAction SilentlyContinue
$html = Join-Path $root 'dist\ClashLabAnnotator_Desktop_v4.html'
$img = Join-Path $root 'android\assets\img'
$models = Join-Path $root 'models'
$main = Join-Path $root 'tools\desktop_app.py'
$args = @(
 '--noconfirm','--onefile','--windowed','--name','ClashLabAnnotator',
 '--add-data',($html + ';.'),
 '--add-data',($img + ';img'),
 '--add-data',((Join-Path $models 'hybrid_gate.onnx') + ';models'),
 '--add-data',((Join-Path $models 'hybrid_emb.onnx') + ';models'),
 '--add-data',((Join-Path $models 'hybrid_protos.npz') + ';models'),
 '--add-data',((Join-Path $models 'hybrid_meta.json') + ';models'),
 '--collect-all','webview','--collect-all','clr_loader','--collect-all','pythonnet',
 '--hidden-import','onnxruntime',
 '--hidden-import','clr','--hidden-import','webview.platforms.edgechromium',
 '--hidden-import','tools.preannotate_core','--hidden-import','clashlab.geo','--hidden-import','clashlab.assets',
 '--exclude-module','torch','--exclude-module','torchvision','--exclude-module','onnx','--exclude-module','onnxscript','--exclude-module','triton',
 '--distpath',(Join-Path $root 'dist_exe'),
 '--workpath',(Join-Path $root 'build_exe'),
 $main
)
& 'D:\Python313\python.exe' -m PyInstaller @args *> 'out\logs\pyinstaller_v16.log'
Write-Output ('build_exit=' + $LASTEXITCODE)
Get-ChildItem 'dist_exe\ClashLabAnnotator.exe' -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ($_.Length.ToString() + " bytes") }