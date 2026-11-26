$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$py = 'D:\Python313\python.exe'
$a = @(
  '--noconfirm','--onefile','--console','--name','ClashOverlayDebug',
  '--collect-data','imgui_bundle','--collect-binaries','glfw','--collect-binaries','imgui_bundle',
  '--collect-data','rapidocr_onnxruntime','--collect-binaries','onnxruntime',
  '--collect-submodules','rapidocr_onnxruntime','--collect-submodules','onnxruntime',
  '--hidden-import','imgui_bundle.python_backends.glfw_backend','--hidden-import','OpenGL.GL','--hidden-import','glfw',
  '--hidden-import','win32gui','--hidden-import','win32con','--hidden-import','win32api','--hidden-import','win32process','--hidden-import','win32ui',
  '--hidden-import','clashlab.vision','--hidden-import','clashlab.ocr_screen','--hidden-import','clashlab.cocapi',
  '--hidden-import','cv2','--hidden-import','numpy','--hidden-import','rapidocr_onnxruntime','--hidden-import','onnxruntime','--hidden-import','onnxruntime.capi._pybind_state',
  '--exclude-module','torch','--exclude-module','torchvision','--exclude-module','torchaudio','--exclude-module','sympy','--exclude-module','networkx','--exclude-module','matplotlib',
  'overlay_exe_main.py'
)
& $py -m PyInstaller @a 2>&1 | Tee-Object -FilePath 'out\logs\build_debug.log'
Write-Output ('debug_build_exit=' + $LASTEXITCODE)
if (Test-Path 'dist\ClashOverlayDebug.exe') { Get-ChildItem 'dist\ClashOverlayDebug.exe' | ForEach-Object { Write-Output ('debug exe ' + $_.Length + ' bytes') } }
