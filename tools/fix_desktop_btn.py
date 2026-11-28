# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_desktop_html.py")
t = open(p, encoding="utf-8").read()
old_add = 't = t.replace(\'<button id="btnExportAll">导出全部</button>\',\n              \'<button id="btnOpenDir" class="sec">导出文件夹</button><button id="btnExportAll">导出全部</button>\', 1)'
new_add = ('t = t.replace(\'<button id="btnExportAll"\', \'<button id="btnOpenDir" class="sec">导出文件夹</button><button id="btnExportAll"\', 1)')
if old_add in t:
    t = t.replace(old_add, new_add, 1); print("btn insert patched")
else:
    print("btn anchor miss")
old_handler = "document.getElementById('btnOpenDir').onclick=function(){"
new_handler = "var odEl=document.getElementById('btnOpenDir');if(odEl)odEl.onclick=function(){"
if old_handler in t:
    t = t.replace(old_handler, new_handler, 1); print("handler guarded")
else:
    print("handler anchor miss")
open(p, "w", encoding="utf-8", newline="\n").write(t)
