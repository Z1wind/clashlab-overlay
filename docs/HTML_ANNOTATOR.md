# 单文件 HTML 标注器 v1.0（与 APK v0.3.0 功能对齐）

## 使用
双击 ClashLabAnnotator_HTML_v1.0.html，用 Edge/Chrome 打开即可（无需安装、无需联网、图片已内嵌）。

## 功能
- 20 张 TH16 满防阵图（base64 内嵌，单文件）
- 四角标定：黄点可拖，可拖到图片外；拖到窗口边缘自动平移
- 双击放大 / ＋－ / 适应；放大后单指拖动平移
- 建筑列表收起为一行「建筑：XX」，点开选类型，选完自动收起；46 类全中文
- 已放建筑可按住拖动调整格位
- 撤销 / 重设四角 / 清空 / 全清空；名称显示开关
- 沿用上张四角；导出本张后自动跳下一张；显示「第 X/20 · 已完成 N」
- 导出 v2 JSON：image / image_size / corners_norm / buildings
- 进度自动存浏览器 localStorage，关掉再开继续

## 导出位置
点「导出本张」或「导出全部」→ 浏览器下载目录得到 annot_bXX.json / annot_all.json

## 验证
- 无头 Edge 渲染：图片内嵌加载正常、网格/角点/面板/进度正常（out/apk_qa/html_selftest5.png）
- 自测：四角→放建筑→导出文档，version=2 / image_size=[1600,735] / image=img/b01.jpg / corners_norm=[0.25,0.25] / buildings=1
- 导出自测：捕获到 a.download=annot_b01.json、href=data:application/json 前缀

## 与 APK 的区别
- 保存位置：浏览器下载目录（APK 是系统下载/私有目录）
- 触控：鼠标拖动 / 滚轮? 目前缩放用按钮与双击（未做滚轮缩放）
