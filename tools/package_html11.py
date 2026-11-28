# -*- coding: utf-8 -*-
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "dist", "html11_selftest.html")
if os.path.exists(p): os.remove(p); print("selftest removed")
main = os.path.join(BASE, "dist", "ClashLabAnnotator_HTML_v1.1.html")
data = open(main, "rb").read(); md5 = hashlib.md5(data).hexdigest()
print("HTML v1.1", len(data), "md5", md5)
lines = [
 "# 单文件 HTML 标注器（桌面版）",
 "",
 "## 当前版本：v1.1（2026-11-28）",
 "文件：dist/ClashLabAnnotator_HTML_v1.1.html",
 format(len(data), ",") + " bytes，md5 " + md5.upper(),
 "",
 "## 操作（鼠标）",
 "- **滚轮**：以指针为中心缩放（0.2x ~ 8x）",
 "- **左键拖动**：平移画面（在空白处按住拖动）",
 "- **左键单击**：点四角 / 放建筑",
 "- 靠近角点按住拖动 = 拖角；靠近已放建筑按住拖动 = 挪建筑",
 "- ＋ / － / 适应 按钮、双击放大也可用",
 "",
 "## 本版修复",
 "- 网格线加亮（青色 .60 透明度、1.3px），四角标定后清晰可见",
 "- 去掉「拖到屏幕边缘自动平移」（桌面改为滚轮+左键拖动）",
 "- 滚轮缩放以指针为中心，缩小可到 0.2x",
 "",
 "## 功能",
 "- 20 张 TH16 满防阵图（base64 内嵌，单文件离线）",
 "- 四角可拖到图片外；46 类中文；类型列表收起、选完自动收起",
 "- 沿用上张四角；导出自动跳下一张；进度「第 X/20 · 已完成 N」",
 "- 导出 v2 JSON 到浏览器下载目录；进度存 localStorage",
 "",
 "## 验证",
 "- 无头 Edge 自测：grid=19143 像素（网格可见）、滚轮后 scale=1.15、左键拖动后 panX=48（平移生效）、corners=4",
 "- 截图：out/apk_qa/html11_selftest.png",
]
open(os.path.join(BASE, "docs", "HTML_ANNOTATOR.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("doc updated")
