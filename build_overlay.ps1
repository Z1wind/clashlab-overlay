# build_overlay.ps1 - package ClashOverlay.exe with PyInstaller (onefile, windowed).
# ASCII only: do NOT add Chinese or non-ASCII characters (PowerShell may parse as GBK).
# Re-runnable: cleans prior build/ and the previous exe before rebuilding.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root
$sw = [System.Diagnostics.Stopwatch]::StartNew()

# Resolve Python: prefer D:\Python313\python.exe, fall back to PATH python.
$py = "D:\Python313\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

# Clean previous artifacts (keep dist directory itself).
if (Test-Path "$root\build") { Remove-Item "$root\build" -Recurse -Force }
if (Test-Path "$root\dist\ClashOverlay.exe") { Remove-Item "$root\dist\ClashOverlay.exe" -Force }

& $py -m PyInstaller --noconfirm --onefile --noconsole --name ClashOverlay `
    --collect-data imgui_bundle `
    --collect-binaries glfw `
    --collect-binaries imgui_bundle `
    --collect-data rapidocr_onnxruntime `
    --collect-submodules rapidocr_onnxruntime `
    --collect-submodules onnxruntime `
    --collect-binaries onnxruntime `
    --hidden-import imgui_bundle.python_backends.glfw_backend `
    --hidden-import OpenGL.GL `
    --hidden-import glfw `
    --hidden-import win32gui `
    --hidden-import win32con `
    --hidden-import win32api `
    --hidden-import win32process `
    --hidden-import win32ui `
    --hidden-import clashlab.vision `
    --hidden-import cv2 `
    --hidden-import numpy `
    --hidden-import rapidocr_onnxruntime `
    --hidden-import onnxruntime `
    --hidden-import onnxruntime.capi._pybind_state `
    --hidden-import clashlab.ocr_screen `
    --hidden-import clashlab.cocapi `
    --hidden-import zhconv `
    --exclude-module torch `
    --exclude-module torchvision `
    --exclude-module torchaudio `
    --exclude-module sympy `
    --exclude-module networkx `
    --exclude-module matplotlib `
    overlay_exe_main.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller exited with $LASTEXITCODE" }
if (-not (Test-Path "$root\dist\ClashOverlay.exe")) { throw "dist\ClashOverlay.exe missing after build" }

$sw.Stop()
$exe = Get-Item "$root\dist\ClashOverlay.exe"
Write-Host ("BUILD OK: {0} ({1:N0} bytes, {2:N1} s)" -f $exe.FullName, $exe.Length, $sw.Elapsed.TotalSeconds)
