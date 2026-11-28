# ClashLab 桌面标注器 v1.1（Windows EXE，无需 Python）

## 运行
双击 ClashLabAnnotator_Desktop_v1.1.exe（单文件，约 20MB）。
**不需要安装 Python**，PyInstaller 已把运行时打进 EXE（已用剥离 PATH 的环境实测）。
首次启动解压 2-4 秒出窗口。

## 电脑操作习惯
- 滚轮：以指针为中心缩放（0.2x-8x）
- 左键拖动空白处：平移画面（光标变抓手）
- 左键单击：点四角 / 放建筑
- 按住角点拖动：拖四角（可拖出图片）
- 按住建筑拖动：挪建筑
- **右键建筑：删除**（光标在建筑上变手型，红色高亮圈）
- Delete：删除悬停建筑；Esc：收起类型面板
- Ctrl+Z 撤销 / Ctrl+Y 重做；Ctrl+S 导出本张；← → 切图
- 底部左侧实时显示「格 x,y | 缩放 %」

## 保存
导出直接写 用户\Downloads\ClashLab标注\（重名自动 _2/_3）；右下「导出文件夹」直接打开。

## 验证
- 无 Python 环境测试：PATH 仅保留 C:\Windows 目录，EXE 启动退出码 0，成功加载 20 图并保存 smoke_test_4.json
- 正常启动：窗口标题 ClashLab 阵型标注（桌面版 v1.1）
- 桌面交互自测：右键删除 afterRightClick=0、坐标 格 18,18、重做按钮存在、无 JS ERR
- 同一页面无头渲染截图：out/apk_qa/desktop_v2_selftest3.png
