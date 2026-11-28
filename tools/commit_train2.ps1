& 'D:\Python313\python.exe' -u 'tools\write_train_report.py'
$g = 'E:\Temp\mingit2\cmd\git.exe'
& $g add -A
& $g commit -m 'feat(ml): train on user 8 real annotations - 6 good bases CV top1 88.2%/top3 94.8%; b01/b02 diagnosed mislabeled' 2>&1 | Select-Object -Last 2