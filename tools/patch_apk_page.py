# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate2.html")
t = open(p, encoding="utf-8").read()
old = "document.getElementById('btnClear').onclick = function(){ if(confirm('清空本张的所有点吗？')){ state[cur]={corners:[],buildings:[]}; draw(); updateUI(); saveLocal(); } };"
new = """var clearArm = false, clearTimer = null;
document.getElementById('btnClear').onclick = function(){
  var btn = this;
  if(!clearArm){
    clearArm = true;
    btn.textContent = '再点一次确认';
    btn.style.background = '#7a2f2f';
    clearTimeout(clearTimer);
    clearTimer = setTimeout(function(){ clearArm = false; btn.textContent = '清空本张'; btn.style.background = ''; }, 3000);
    return;
  }
  clearArm = false; clearTimeout(clearTimer);
  btn.textContent = '清空本张'; btn.style.background = '';
  state[cur] = {corners:[], buildings:[]};
  draw(); updateUI(); saveLocal(); toast('已清空本张');
};"""
if old in t:
    t = t.replace(old, new, 1)
else:
    print("clear anchor miss")
# 首次启动自动打开教程
old2 = "loadLocal(); buildPalette(); loadImage(0);"
new2 = """loadLocal(); buildPalette(); loadImage(0);
try{
  if(!localStorage.getItem('clashlab_seen_help')){
    document.getElementById('help').style.display = 'block';
    localStorage.setItem('clashlab_seen_help', '1');
  }
}catch(e){}"""
if old2 in t:
    t = t.replace(old2, new2, 1)
else:
    print("help-first-run anchor miss")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("page patched", len(t))
