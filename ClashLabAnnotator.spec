# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat/dist/ClashLabAnnotator_Desktop_v3.html', '.'), ('C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat/android/assets/img', 'img'), ('C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat/models/hybrid_gate.onnx', 'models'), ('C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat/models/hybrid_emb.onnx', 'models'), ('C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat/models/hybrid_protos.npz', 'models'), ('C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat/models/hybrid_meta.json', 'models')]
binaries = []
hiddenimports = ['onnxruntime', 'clr', 'webview.platforms.edgechromium', 'tools.preannotate_core', 'clashlab.geo', 'clashlab.assets']
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('clr_loader')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pythonnet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:/Users/Admin（无密码）/Doubao/chats/2026-11-23/new-chat/tools/desktop_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'onnx', 'onnxscript', 'triton'],
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
    name='ClashLabAnnotator',
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
