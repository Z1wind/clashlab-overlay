@echo off
chcp 65001 >nul
cd /d "C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
echo 标注服务已启动，浏览器应会自动打开。
echo 若没自动打开，手动访问：http://127.0.0.1:8791/out/overlay/_recog_mx/annotate.html
echo 关掉这个黑窗口就会停止服务。
start "" "http://127.0.0.1:8791/out/overlay/_recog_mx/annotate.html"
"D:\Python313\python.exe" -m http.server 8791 --bind 127.0.0.1
pause
