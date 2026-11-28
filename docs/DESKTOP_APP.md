# ClashLab 桌面标注器 v1.0（Windows EXE）

## 运行
双击 ClashLabAnnotator_Desktop_v1.0.exe（单文件，约 20MB，无需安装 Python/浏览器）。
首次启动会解压到临时目录，约 2-4 秒出窗口。

## 操作（鼠标）
- 滚轮：以指针为中心缩放
- 左键拖动空白处：平移画面
- 左键单击：点四角 / 放建筑
- 按住角点拖动：拖四角（可拖出图片外）
- 按住已放建筑拖动：挪建筑
- Ctrl+Z 撤销；Ctrl+S 导出本张；← → 切图

## 保存位置
导出写到 用户\Downloads\ClashLab标注\（重名自动加 _2/_3）。
右下角「导出文件夹」按钮可直接打开该目录。

## 与网页版区别
- 原生窗口（WebView2），无浏览器标签/地址栏
- 导出直接落盘并显示完整路径（网页版走浏览器下载）
- 附带「导出文件夹」按钮与快捷键

## 验证
- 构建：PyInstaller onefile + pywebview(WebView2)
- 快速验证：程序启动→加载 20 张图→JS 桥保存 smoke_test_3.json 到 Downloads\ClashLab标注\（返回 ok）
- 进程窗口标题：ClashLab 阵型标注（桌面版）
- 同一 HTML 无头渲染：无 JS 错误、图片/网格/按钮正常（out/apk_qa/desktop_html_check.png）
