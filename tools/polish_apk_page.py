# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate2.html")
t = open(p, encoding="utf-8").read()
# 1) 确认延时 3s -> 6s
t = t.replace("}, 3000);", "}, 6000);")
# 2) 导出提示友好化
t = t.replace("""  var name = 'annot_b' + (cur+1 < 10 ? '0' + (cur+1) : (cur+1)) + '.json';
  if(window.AndroidBridge && window.AndroidBridge.saveFile){
    toast(window.AndroidBridge.saveFile(name, JSON.stringify(doc)));
  } else {""",
"""  var name = 'annot_b' + (cur+1 < 10 ? '0' + (cur+1) : (cur+1)) + '.json';
  if(window.AndroidBridge && window.AndroidBridge.saveFile){
    var r = window.AndroidBridge.saveFile(name, JSON.stringify(doc));
    if(r && r.indexOf('OK:') === 0){ toast('已保存到下载目录：' + name); }
    else if(r && r.indexOf('OK') === 0){ toast('已保存到 App 目录：' + name + '（文件管理里 Android/data/com.clashlab.annotator 下）'); }
    else { toast('保存失败：' + r); }
  } else {""")
t = t.replace("""  if(window.AndroidBridge && window.AndroidBridge.saveFile){
    toast(window.AndroidBridge.saveFile('annot_all.json', JSON.stringify(all)));
  } else {""",
"""  if(window.AndroidBridge && window.AndroidBridge.saveFile){
    var r2 = window.AndroidBridge.saveFile('annot_all.json', JSON.stringify(all));
    if(r2 && r2.indexOf('OK:') === 0){ toast('已保存到下载目录：annot_all.json'); }
    else if(r2 && r2.indexOf('OK') === 0){ toast('已保存到 App 目录：annot_all.json'); }
    else { toast('保存失败：' + r2); }
  } else {""")
# 3) 帮助里补一句权限提示
t = t.replace("<b>导出：</b>「导出本张」保存 JSON；「导出全部」把 20 张一起导出。",
              "<b>导出：</b>「导出本张」保存 JSON；「导出全部」把 20 张一起导出。<br>如果第一次打开弹出「允许访问文件」，请点 <b>允许</b>，导出的 JSON 才会出现在「下载」里。")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("page polished", len(t))
