$files = @()
$files += (Join-Path $env:USERPROFILE 'Downloads\annot_b01 (1).json')
$files += (Join-Path $env:USERPROFILE 'Downloads\annot_b02 (1).json')
for ($i=3; $i -le 8; $i++) { $files += (Join-Path $env:USERPROFILE ('Downloads\annot_b{0:D2}.json' -f $i)) }
& 'D:\Python313\python.exe' -u 'tools\label_qa.py' --labels ($files -join ';')