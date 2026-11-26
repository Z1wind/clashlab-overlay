# -*- coding: utf-8 -*-
"""创建/更新 GitHub 个人主页仓库 Z1wind/Z1wind 的 README。"""
import base64, json, os, urllib.error, urllib.request
TOKEN = os.environ["GH_TOKEN"]
API = "https://api.github.com"

def call(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    if data is not None:
        h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=60) as r:
            b = r.read().decode("utf-8", "ignore")
            return r.status, (json.loads(b) if b else {})
    except urllib.error.HTTPError as e:
        return e.code, {"_body": e.read().decode("utf-8", "ignore")[:300]}

status, repo = call("GET", API + "/repos/Z1wind/Z1wind")
print("profile repo:", status)
if status == 404:
    status, repo = call("POST", API + "/user/repos", {
        "name": "Z1wind", "description": "GitHub profile", "private": False, "auto_init": False})
    print("create repo:", status, repo.get("full_name") or repo.get("_body"))

readme = """# Hi, I'm Z1wind 👋

**太原理工大学 · 材料科学在读** / Materials Science @ Taiyuan University of Technology

课余时间做点电脑程序研究和游戏玩法优化，喜欢把「看得见的操作」变成「能算清楚的数据」。

## 关于我

- 🎓 太原理工大学材料科学在读
- 💻 课余进行电脑程序的研究和游戏玩法优化
- 🎮 折腾 Clash of Clans 阵型分析：截图 → 44×44 标定 → 布局评分 → 弱点 → 战术图 / 2D 推演（开源：[ClashLab](https://github.com/Z1wind/clashlab-overlay)）
- 🤝 欢迎联系、交流，甚至可以一起玩游戏

## 联系我

| 方式 | 地址 |
|---|---|
| 邮箱 | 1808016780@qq.com |
| 备用邮箱 | 141kw.shop@gmail.com |
| Discord | https://discord.gg/HVh8KdNM |
| X / Twitter | [@standkeepmoving](https://x.com/standkeepmoving) |

## 在做的事

- [ClashLab](https://github.com/Z1wind/clashlab-overlay)：以 LLM 为辅的部落冲突布阵研究器，MIT 开源
- 学习 / 试验：计算机视觉、小模型训练、游戏内数据可视化

> 欢迎提 issue、聊想法，或者单纯来一起打一把。

## 联系我

| 方式 | 地址 |
|---|---|
| 邮箱 | 1808016780@qq.com |
| 备用邮箱 | 141kw.shop@gmail.com |
| Discord | https://discord.gg/HVh8KdNM |
| X / Twitter | @standkeepmoving |
"""
readme = """# Hi, I'm Z1wind 👋

**太原理工大学 · 材料科学在读** / Materials Science @ Taiyuan University of Technology

课余时间做点电脑程序研究和游戏玩法优化，喜欢把「看得见的操作」变成「能算清楚的数据」。

## 关于我

- 🎓 太原理工大学材料科学在读
- 💻 课余进行电脑程序的研究和游戏玩法优化
- 🎮 折腾 Clash of Clans 阵型分析：截图 → 44×44 标定 → 布局评分 → 弱点 → 战术图 / 2D 推演（开源：[ClashLab](https://github.com/Z1wind/clashlab-overlay)）
- 🤝 欢迎联系、交流，甚至可以一起玩游戏

## 联系我

| 方式 | 地址 |
|---|---|
| 邮箱 | 1808016780@qq.com |
| 备用邮箱 | 141kw.shop@gmail.com |
| Discord | https://discord.gg/HVh8KdNM |
| X / Twitter | [@standkeepmoving](https://x.com/standkeepmoving) |

## 在做的事

- [ClashLab](https://github.com/Z1wind/clashlab-overlay)：以 LLM 为辅的部落冲突布阵研究器，MIT 开源
- 学习 / 试验：计算机视觉、小模型训练、游戏内数据可视化

> 欢迎提 issue、聊想法，或者单纯来一起打一把。
"""
status, cur = call("GET", API + "/repos/Z1wind/Z1wind/contents/README.md")
payload = {"message": "Add profile README", "content": base64.b64encode(readme.encode()).decode(), "branch": "main"}
if status == 200 and cur.get("sha"):
    payload["sha"] = cur["sha"]
status, r = call("PUT", API + "/repos/Z1wind/Z1wind/contents/README.md", payload)
print("put readme:", status, r.get("commit", {}).get("sha") or r.get("_body"))
