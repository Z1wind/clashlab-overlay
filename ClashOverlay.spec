# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules

datas = []
binaries = []
hiddenimports = ['imgui_bundle.python_backends.glfw_backend', 'OpenGL.GL', 'glfw', 'win32gui', 'win32con', 'win32api', 'win32process', 'win32ui', 'clashlab.vision', 'cv2', 'numpy', 'rapidocr_onnxruntime', 'onnxruntime', 'onnxruntime.capi._pybind_state', 'clashlab.ocr_screen', 'clashlab.cocapi', 'zhconv']
datas += collect_data_files('imgui_bundle')
datas += collect_data_files('rapidocr_onnxruntime')
datas += collect_data_files('zhconv')
binaries += collect_dynamic_libs('glfw')
binaries += collect_dynamic_libs('imgui_bundle')
binaries += collect_dynamic_libs('onnxruntime')
hiddenimports += collect_submodules('rapidocr_onnxruntime')
hiddenimports += collect_submodules('onnxruntime')


a = Analysis(
    ['overlay_exe_main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'torchaudio', 'sympy', 'networkx', 'matplotlib'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ClashOverlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
