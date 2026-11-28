& 'D:\Python313\python.exe' -u 'tools\reexport_onnx.py' 2>$null | Select-String -Pattern 're-exported|batch5' | ForEach-Object { $_.Line }
& 'D:\Python313\python.exe' -u 'tools\dump_types.py'
Get-ChildItem 'models\pipeline_gate.onnx','models\pipeline_type.onnx','models\pipeline_types.json' | ForEach-Object { Write-Output ($_.Name + " " + $_.Length + " bytes") }
# 重打包 EXE v1.4
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build_exe_v13.ps1