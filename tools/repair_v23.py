# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "android", "assets", "annotate4.html")
t = open(p, encoding="utf-8").read()
anchor = "cv.addEventListener('mousedown',onDown);"
block = '''function updateUI(){var s=S();document.getElementById('count').textContent='已标 '+s.buildings.length;
  var a=document.getElementById('st1'),b=document.getElementById('st2'),c=document.getElementById('st3');
  a.className=s.corners.length<4?'on':'';b.className=(s.corners.length===4&&s.buildings.length===0)?'on':'';c.className=(s.corners.length===4&&s.buildings.length>0)?'on':'';
  if(s.corners.length<4)document.getElementById('hint').textContent='点四个角（已点 '+s.corners.length+'/4，黄点可拖，＋－缩放）';
  document.getElementById('pal').style.display=s.corners.length<4?'none':'block';}
function buildPalette(){var tabs=document.getElementById('cattabs'),types=document.getElementById('types');tabs.innerHTML='';types.innerHTML='';
  CATS.forEach(function(cat,ci){var b=document.createElement('button');b.textContent=cat[0];if(ci===catIdx)b.className='on';b.onclick=function(){catIdx=ci;buildPalette();};tabs.appendChild(b);});
  CATS[catIdx][1].forEach(function(t){var b=document.createElement('button');b.textContent=(SNAME[t]||t);if(t===sel)b.className='on';b.onclick=function(){sel=t;buildPalette();toast('已选中：'+(CNAME[t]||t));};types.appendChild(b);});}
function saveDoc(s,imgPath){return {version:2,image:imgPath,image_size:[img.naturalWidth,img.naturalHeight],grid:44,
  corners_norm:s.corners.map(function(p){return [p[0],p[1]];}),
  corners:s.corners.map(function(p){return [p[0]*img.naturalWidth,p[1]*img.naturalHeight];}),
  buildings:s.buildings.map(function(b){return{type:b.type,name:CNAME[b.type]||b.type,tile:b.tile};})};}
function exportOne(){var s=S();if(s.corners.length<4){toast('还没点四个角，不能导出');return;}var doc=saveDoc(s,IMAGES[cur]);doc.saved_at=new Date().toISOString();var name='annot_b'+(cur+1<10?'0'+(cur+1):(cur+1))+'.json';
  if(window.AndroidBridge&&window.AndroidBridge.saveFile){var r=window.AndroidBridge.saveFile(name,JSON.stringify(doc));if(r&&r.indexOf('OK:')===0)toast('已保存到下载：'+name);else if(r&&r.indexOf('OK')===0)toast('已保存到 App 目录：'+name);else toast('保存失败：'+r);}else{var a=document.createElement('a');a.href='data:application/json;charset=utf-8,'+encodeURIComponent(JSON.stringify(doc));a.download=name;a.click();toast('已导出 '+name);}}
function exportAll(){var docs=[];for(var i=0;i<IMAGES.length;i++){var s=state[i];if(s&&s.corners.length===4)docs.push(saveDoc(s,IMAGES[i]));}if(!docs.length){toast('还没有任何一张完成标定');return;}var all={version:2,count:docs.length,bases:docs};
  if(window.AndroidBridge&&window.AndroidBridge.saveFile){var r=window.AndroidBridge.saveFile('annot_all.json',JSON.stringify(all));if(r&&r.indexOf('OK:')===0)toast('已保存到下载：annot_all.json');else if(r&&r.indexOf('OK')===0)toast('已保存到 App 目录：annot_all.json');else toast('保存失败：'+r);}else{var a=document.createElement('a');a.href='data:application/json;charset=utf-8,'+encodeURIComponent(JSON.stringify(all));a.download='annot_all.json';a.click();toast('已导出全部');}}
function loadImage(idx){cur=idx;document.getElementById('tip').textContent='第 '+(idx+1)+'/'+IMAGES.length+' 张';
  img.onload=function(){view={scale:1,panX:0,panY:0};fitCanvas();draw();updateUI();};img.src=IMAGES[idx];updateUI();}
document.getElementById('btnUndo').onclick=function(){var s=S();if(s.buildings.length)s.buildings.pop();else if(s.corners.length)s.corners.pop();draw();updateUI();saveLocal();toast('已撤销');};
document.getElementById('btnReset').onclick=function(){S().corners=[];S().buildings=[];draw();updateUI();saveLocal();toast('已重设四角');};
var clearArm=false,clearTimer=null;
document.getElementById('btnClear').onclick=function(){var btn=this;if(!clearArm){clearArm=true;btn.textContent='再点确认';clearTimeout(clearTimer);clearTimer=setTimeout(function(){clearArm=false;btn.textContent='清空';},6000);return;}clearArm=false;clearTimeout(clearTimer);btn.textContent='清空';state[cur]={corners:[],buildings:[]};draw();updateUI();saveLocal();toast('已清空本张');};
document.getElementById('btnNames').onclick=function(){showNames=!showNames;this.textContent='名称:'+(showNames?'开':'关');draw();};
document.getElementById('btnNext').onclick=function(){saveLocal();if(cur<IMAGES.length-1)loadImage(cur+1);else toast('已经是最后一张');};
document.getElementById('btnPrev').onclick=function(){saveLocal();if(cur>0)loadImage(cur-1);else toast('已经是第一张');};
document.getElementById('btnExport').onclick=exportOne;document.getElementById('btnExportAll').onclick=exportAll;
document.getElementById('btnHelp').onclick=function(){document.getElementById('help').style.display='block';};
document.getElementById('btnHelpOk').onclick=function(){document.getElementById('help').style.display='none';};
document.getElementById('btnZoomIn').onclick=function(){view.scale=Math.min(6,view.scale*1.35);draw();toast('放大 x'+view.scale.toFixed(1));};
document.getElementById('btnZoomOut').onclick=function(){view.scale=Math.max(1,view.scale/1.35);if(view.scale===1){view.panX=0;view.panY=0;}draw();toast('缩放 x'+view.scale.toFixed(1));};
document.getElementById('btnZoomFit').onclick=function(){view={scale:1,panX:0,panY:0};draw();toast('已适应屏幕');};
var palHidden=false;
document.getElementById('btnPalHide').onclick=function(){palHidden=!palHidden;var pal=document.getElementById('pal');
  pal.querySelector('#cattabs').style.display=palHidden?'none':'flex';
  pal.querySelector('#types').style.display=palHidden?'none':'flex';
  this.textContent=palHidden?'展开':'收';};
'''
if "function updateUI" not in t and anchor in t:
    t = t.replace(anchor, block + "\n" + anchor, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("missing block restored; size", len(t))
else:
    print("already has updateUI or anchor miss", ("function updateUI" in t), (anchor in t))
