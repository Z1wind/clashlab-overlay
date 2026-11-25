# -*- coding: utf-8 -*-
"""英雄装备画像 / 参考打法卡库 / 赛前简报（第一阶段准备层，暂不接主窗口）。

边界：
- 本模块只提供数据读写、纯函数与 Tk 控件构建，不反向导入 app.py / ui.py；
- 只依赖标准库（tkinter, json, os, re, webbrowser）+ 工程已有的 Pillow，不引入新依赖；
- 视觉识别候选的低置信标记（tag_low_confidence）是纯函数，绝不自动写入 profile。

第二阶段由 app.py / ui.py 调用本模块的构建函数与纯函数。
"""
import json
import os
import re
import webbrowser

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageDraw, ImageFont, ImageTk

# ---------------- 路径与常量 ----------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EQUIPMENT_DIR = os.path.join(ROOT, "assets", "coc", "equipment")
HEROES_JSON = os.path.join(ROOT, "config", "heroes.json")
INDEX_DEMO = os.path.join(ROOT, "knowledge", "index_demo.json")

# 与 plan_marks.HERO_ROLES 对齐：queen / king / warden / rc
HERO_META = {
    "queen": ("女王", 90),
    "king": ("蛮王", 85),
    "warden": ("守护者", 75),
    "rc": ("冠军", 30),
}

# 内置装备表：assets/coc/equipment 图标目录缺失时回退。
# (id, 中文名, 归属英雄)；扫描到的图标文件没有归属时 hero 为空。
BUILTIN_EQUIPMENT = [
    ("giant-arrow", "巨型箭", "queen"),
    ("invisibility-vial", "隐身药水", "queen"),
    ("vampire-stache", "吸血鬼胡子", "queen"),
    ("spiky-ball", "尖刺球", "king"),
    ("seeking-shield", "追踪盾", "king"),
    ("earthquake-boots", "地震靴", "warden"),
    ("eternal-tome", "永恒之书", "warden"),
    ("healing-tome", "治疗之书", "warden"),
    ("royal-cloak", "皇家斗篷", "rc"),
    ("hog-rider", "野猪骑手", "rc"),
]

# 已知装备 id → 中文名（扫描到真实图标文件时也用于补标签；未收录回退为 id 本身）
EQUIPMENT_CN = {
    "giant-arrow": "巨型箭",
    "invisibility-vial": "隐身药水",
    "vampire-stache": "吸血鬼胡子",
    "spiky-ball": "尖刺球",
    "seeking-shield": "追踪盾",
    "earthquake-boots": "地震靴",
    "eternal-tome": "永恒之书",
    "healing-tome": "治疗之书",
    "royal-cloak": "皇家斗篷",
    "hog-rider": "野猪骑手",
    "archer-puppet": "弓手木偶",
    "barbarian-puppet": "蛮兵木偶",
    "fireball": "火球",
    "frozen-arrow": "冰冻箭",
    "giant-gauntlet": "巨型拳套",
    "haste-vial": "急速药水",
    "healer-puppet": "治疗木偶",
    "hog-rider-puppet": "野猪木偶",
    "life-gem": "生命宝石",
    "magic-mirror": "魔镜",
    "rage-gem": "狂暴宝石",
    "rage-vial": "狂暴药水",
    "rocket-spear": "火箭矛",
    "royal-gem": "皇家宝石",
    "snake-bracelet": "蛇镯",
    "stick-horse": "竹马",
    "vampstache": "吸血鬼胡子",
}

# 调色板（与 app.py / ui.py 对齐：深底 + 青/琥珀，避免大面积紫）
CARD_BG = "#12181d"
CARD_HI = "#182128"
LINE = "#28333c"
INK = "#eef1f4"
GREY = "#94a0a8"
DIM = "#63707a"
CYAN = "#5ed6d6"
AMBER = "#f0c452"
CORAL = "#e87460"
GREEN = "#60c882"

REF_RE = re.compile(r"\[([A-Za-z]+\d+)\]")


# ---------------- 画像读写（config/heroes.json） ----------------

def default_profile(th=13):
    """空画像骨架：th + 四英雄（等级取默认、装备空）。"""
    return {
        "th": th,
        "heroes": {
            role: {"level": meta[1], "equipment": []}
            for role, meta in HERO_META.items()
        },
    }


def load_profile(path=HEROES_JSON):
    """读 config/heroes.json；文件缺失时返回默认骨架。缺字段按默认补齐。"""
    prof = default_profile()
    if not os.path.exists(path):
        return prof
    with open(path, encoding="utf-8") as f:
        data = json.load(f) or {}
    prof["th"] = int(data.get("th", 13) or 13)
    raw_heroes = data.get("heroes") or {}
    for role, meta in HERO_META.items():
        h = raw_heroes.get(role) or {}
        try:
            level = int(h.get("level", meta[1]) or meta[1])
        except (TypeError, ValueError):
            level = meta[1]
        prof["heroes"][role] = {
            "level": level,
            "equipment": [str(x) for x in (h.get("equipment") or []) if str(x).strip()],
        }
    return prof


def save_profile(profile, path=HEROES_JSON):
    """画像落盘 UTF-8 JSON（缩进 2 空格），自动建父目录。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    return path


# ---------------- 装备候选 ----------------

def _cn_of(eid):
    return EQUIPMENT_CN.get(eid, eid.replace("-", " "))


def equipment_label(eid):
    """装备 id → 中文名（公开别名，供外部展示用）。"""
    return _cn_of(eid)


# ---------------- used/missing（UI 层自算，纯展示，不参与算法） ----------------

# TH13 基准最少必需装备表；卡库存在时会被卡的 equipment 标签并集覆盖。
REQUIRED_EQUIPMENT = [
    "giant-arrow", "invisibility-vial", "spiky-ball", "seeking-shield",
    "eternal-tome", "healing-tome", "earthquake-boots", "royal-cloak",
]


def _equipped_set(profile):
    out = set()
    for h in (profile or {}).get("heroes", {}).values():
        out.update(h.get("equipment") or [])
    return out


def required_set(cards=None, required=None):
    """必需装备集合：显式 required > 卡库 equipment 标签并集 > 内置基准表。"""
    if required:
        return set(required)
    out = set()
    for c in cards or []:
        out.update(c.get("equipment") or [])
    return out or set(REQUIRED_EQUIPMENT)


def compute_used_missing(profile, cards=None, required=None):
    """UI 层对照画像装备与必需表，算 used（已具备）/missing（缺）。纯展示。

    返回 {"used":[{"id","label"}], "missing":[{"id","label"}],
          "equipped":[{"id","label"}] 全部已选}。
    """
    need = required_set(cards, required)
    have = _equipped_set(profile)
    used = [{"id": i, "label": _cn_of(i)} for i in sorted(need & have)]
    missing = [{"id": i, "label": _cn_of(i)} for i in sorted(need - have)]
    equipped = [{"id": i, "label": _cn_of(i)} for i in sorted(have)]
    return {"used": used, "missing": missing, "equipped": equipped}


def profile_summary_line(profile):
    """面板底部小字：女王:巨型箭+隐身药水 | 蛮王:尖刺球+追踪盾（无装备的英雄不显示）。"""
    parts = []
    for role, (name, _lv) in HERO_META.items():
        eq = profile.get("heroes", {}).get(role, {}).get("equipment") or []
        if eq:
            parts.append(f"{name}:" + "+".join(_cn_of(e) for e in eq))
    return " | ".join(parts)


def card_refs_line(cards):
    """参考卡 id 串：[k012][k031]；无卡返回 ''。"""
    ids = [c.get("id") for c in (cards or []) if c.get("id")]
    return "".join(f"[{i}]" for i in ids)


def panel_footer(profile, cards=None):
    """标注面板底部小字：画像 女王:... | 参考 [k012]。缺段自动省略。"""
    seg = []
    line = profile_summary_line(profile)
    if line:
        seg.append("画像 " + line)
    refs = card_refs_line(cards)
    if refs:
        seg.append("参考 " + refs)
    return " | ".join(seg)


def equipment_candidates(assets_dir=EQUIPMENT_DIR):
    """优先扫 assets/coc/equipment/*.png 文件名生成候选；目录缺失/为空回退内置常量。

    返回 [{"id", "label", "hero"}]，扫描项 hero 为 ""。
    """
    out = []
    if os.path.isdir(assets_dir):
        for fn in sorted(os.listdir(assets_dir)):
            if fn.lower().endswith(".png"):
                cid = os.path.splitext(fn)[0]
                out.append({"id": cid, "label": _cn_of(cid), "hero": ""})
    if out:
        return out
    return [{"id": i, "label": label, "hero": hero} for i, label, hero in BUILTIN_EQUIPMENT]


def load_equipment_icons(dir_path=EQUIPMENT_DIR, size=40):
    """扫描装备图标并缩放到边长 size 缓存为 PIL.Image；目录缺失/无图返回 {}。

    返回 {id: PIL.Image}（RGBA），调用方自行转 ImageTk.PhotoImage；
    返回空时调用方必须走文字按钮回退，禁止出现空白方块。
    """
    icons = {}
    if not os.path.isdir(dir_path):
        return icons
    for fn in sorted(os.listdir(dir_path)):
        if not fn.lower().endswith(".png"):
            continue
        cid = os.path.splitext(fn)[0]
        try:
            im = Image.open(os.path.join(dir_path, fn)).convert("RGBA")
            im.thumbnail((size, size), Image.LANCZOS)
            icons[cid] = im
        except Exception:
            continue
    return icons


# ---------------- 低置信标记（纯函数，不写 profile） ----------------

def tag_low_confidence(cands, threshold=0.7):
    """视觉识别候选打分：score/confidence < threshold 标 "待确认"，>= 标 "ok"。

    纯函数：返回新列表（每个 dict 补 score/tag），原列表不动，绝不写入 profile。
    """
    out = []
    for c in cands or []:
        c = dict(c)
        score = float(c.get("score", c.get("confidence", 0.0)) or 0.0)
        c["score"] = score
        c["tag"] = "待确认" if score < threshold else "ok"
        out.append(c)
    return out


# ---------------- 卡库（knowledge/index*.json） ----------------

def load_cards(path=INDEX_DEMO):
    """读卡库 JSON：接受 {"cards": [...]} 或裸列表；文件缺失返回 []。"""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        cards = data.get("cards") or []
    elif isinstance(data, list):
        cards = data
    else:
        cards = []
    return [c for c in cards if isinstance(c, dict)]


def filter_cards(cards, pattern=None, equipment=None):
    """按 pattern 精确匹配 / equipment 标签包含过滤；None 不过滤。"""
    out = []
    for c in cards or []:
        if pattern and c.get("pattern") != pattern:
            continue
        if equipment and equipment not in (c.get("equipment") or []):
            continue
        out.append(c)
    return out


def card_title_line(card):
    """[k012] 穿云箭三防空 · bilibili · 2024-06 · 置信 0.72"""
    sid = card.get("id", "?")
    title = card.get("title", "未命名")
    src = card.get("source")
    if isinstance(src, dict):
        src = src.get("name") or src.get("url") or "-"
    src = src or "-"
    date = card.get("date", "?")
    conf = card.get("confidence", card.get("score"))
    conf_s = f"{float(conf):.2f}" if isinstance(conf, (int, float)) else "?"
    return f"[{sid}] {title} · {src} · {date} · 置信 {conf_s}"


# ---------------- Tk 控件：装备图标网格 ----------------

def build_icon_grid(parent, candidates, selected, on_toggle, icons=None, cols=6, size=40):
    """装备图标网格多选；无图标自动降级为文字按钮（不画空白方块）。

    candidates: [{"id","label","hero"?}]；selected: 可迭代已选 id；
    on_toggle(id, checked: bool)；icons: {id: PIL.Image}，不传则内部加载。
    返回 (frame, state)；state.sel 为当前已选 id 集合，state.buttons 为按钮。
    """
    selected = set(selected or [])
    if icons is None:
        icons = load_equipment_icons(size=size)
    has_icons = bool(icons)

    grid = tk.Frame(parent, bg=CARD_BG)
    state = {"buttons": {}, "icons": {}, "sel": set(selected)}
    tooltip = {"win": None}

    def hide_tip():
        if tooltip["win"] is not None:
            tooltip["win"].destroy()
            tooltip["win"] = None

    def show_tip(btn, label):
        hide_tip()
        x = btn.winfo_rootx() + size // 2
        y = btn.winfo_rooty() + size + 4
        tw = tk.Toplevel(btn)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.geometry(f"+{x}+{y}")
        tk.Label(tw, text=label, bg="#0d1114", fg=INK, padx=8, pady=3,
                 font=("Microsoft YaHei", 9), relief="solid", bd=1).pack()
        tooltip["win"] = tw

    def _paint(btn, cid):
        on = cid in state["sel"]
        if has_icons and icons.get(cid) is not None:
            btn.configure(bg=("#22383f" if on else CARD_HI),
                          highlightbackground=(CYAN if on else LINE),
                          highlightthickness=(2 if on else 1))
        else:
            btn.configure(bg=("#22383f" if on else CARD_HI),
                          fg=(CYAN if on else INK))

    for i, c in enumerate(candidates):
        cid, label = c["id"], c["label"]
        col, row = i % cols, i // cols
        photo = icons.get(cid) if has_icons else None
        if photo is not None:
            state["icons"][cid] = ImageTk.PhotoImage(photo)
            btn = tk.Button(grid, image=state["icons"][cid],
                            width=size + 12, height=size + 16,
                            bg=CARD_HI, activebackground="#22383f",
                            bd=0, relief="flat",
                            highlightbackground=LINE, highlightthickness=1)
        else:
            btn = tk.Button(grid, text=label, width=11, bg=CARD_HI, fg=INK,
                            activebackground="#22383f", activeforeground=CYAN,
                            bd=0, relief="flat", font=("Microsoft YaHei", 9),
                            padx=6, pady=5)
        btn.grid(row=row, column=col, padx=6, pady=6, sticky="nw")
        btn.bind("<Enter>", lambda e, b=btn, l=label: show_tip(b, l))
        btn.bind("<Leave>", lambda e: hide_tip())

        def _toggle(_ev=None, cid=cid, btn=btn):
            now = cid in state["sel"]
            if now:
                state["sel"].discard(cid)
            else:
                state["sel"].add(cid)
            _paint(btn, cid)
            on_toggle(cid, not now)

        btn.configure(command=_toggle)
        state["buttons"][cid] = btn
        _paint(btn, cid)

    return grid, state


# ---------------- Tk 控件：英雄装备画像区 ----------------

def build_profile_widgets(parent, profile, on_change, icons=None):
    """四英雄各一块：等级输入 + 装备图标网格。宽松竖排，不挤。

    on_change(role, level:int, equipment:list[str]) 在等级/装备变化时回调。
    返回 {role: {"frame", "level_var", "grid_state"}}。
    """
    candidates = equipment_candidates()
    widgets = {}
    outer = tk.Frame(parent, bg=CARD_BG)

    for role, (name, _def_level) in HERO_META.items():
        h = profile["heroes"].get(role, {})
        equip = list(h.get("equipment") or [])

        card = tk.Frame(outer, bg=CARD_BG, highlightbackground=LINE,
                        highlightthickness=1)
        card.pack(fill="x", padx=12, pady=8)

        head = tk.Frame(card, bg=CARD_BG)
        head.pack(fill="x", padx=12, pady=(10, 2))
        tk.Label(head, text=name, bg=CARD_BG, fg=INK,
                 font=("Microsoft YaHei", 11, "bold")).pack(side="left")
        tk.Label(head, text="Lv.", bg=CARD_BG, fg=GREY,
                 font=("Microsoft YaHei", 9)).pack(side="left", padx=(14, 4))
        level_var = tk.StringVar(value=str(h.get("level", _def_level)))
        e_level = ttk.Entry(head, width=5, textvariable=level_var)
        e_level.pack(side="left")

        def _changed(role=role, level_var=level_var):
            try:
                level = int(level_var.get().strip() or _def_level)
            except ValueError:
                level = _def_level
            on_change(role, level, sorted(widgets[role]["grid_state"].sel))

        e_level.bind("<KeyRelease>", lambda ev, r=role: _changed(r))

        grid, gstate = build_icon_grid(card, candidates, equip,
                                       lambda cid, checked, r=role: _changed(r),
                                       icons=icons)
        grid.pack(fill="x", padx=12, pady=(4, 10))
        widgets[role] = {"frame": card, "level_var": level_var,
                         "grid_state": gstate}

    return outer, widgets


# ---------------- Tk 控件：参考打法卡库区 ----------------

def build_cards_widgets(parent, cards, on_select, open_url=None):
    """卡库列表（[k012] 标题 · 来源 · 日期 · 置信）+ pattern/装备过滤 + 详情。

    不抓网页：open_url(url) 由调用方注入；不传则默认 webbrowser.open。
    on_select(card) 选中回调。返回 {"frame","listbox","detail","url_btn"}。
    """
    cards = cards or []
    opener = open_url or webbrowser.open
    wrap = tk.Frame(parent, bg=CARD_BG)

    bar = tk.Frame(wrap, bg=CARD_BG)
    bar.pack(fill="x", padx=12, pady=(12, 4))
    tk.Label(bar, text="过滤", bg=CARD_BG, fg=GREY,
             font=("Microsoft YaHei", 9)).pack(side="left")
    patterns = sorted({c.get("pattern") for c in cards if c.get("pattern")})
    equips = sorted({e for c in cards for e in (c.get("equipment") or [])})
    filter_values = ["全部"] + patterns + [f"装备:{e}" for e in equips]
    filter_var = tk.StringVar(value="全部")
    cb = ttk.Combobox(bar, state="readonly", width=18, values=filter_values,
                       textvariable=filter_var)
    cb.pack(side="left", padx=8)

    lb = tk.Listbox(wrap, height=8, bg="#0d1114", fg=INK, selectbackground="#22383f",
                    selectforeground=CYAN, bd=0, highlightthickness=0,
                    font=("Microsoft YaHei", 10), activestyle="none")
    lb.pack(fill="x", padx=12, pady=6)

    detail = tk.Text(wrap, height=7, bg="#0d1114", fg=INK, bd=0,
                     font=("Microsoft YaHei", 10), wrap="word",
                     insertbackground=INK)
    detail.pack(fill="both", expand=True, padx=12, pady=(2, 4))
    detail.tag_configure("ref", foreground=CYAN)
    detail.tag_configure("label", foreground=GREY)

    url_btn = ttk.Button(wrap, text="打开来源", state="disabled")
    url_btn.pack(anchor="e", padx=12, pady=(0, 12))

    state = {"current": None}

    def _render_detail(card):
        detail.delete("1.0", "end")
        src = card.get("source")
        url = src.get("url") if isinstance(src, dict) else (src or "")
        kps = card.get("key_points") or []
        detail.insert("end", "要点：\n", "label")
        for kp in kps:
            detail.insert("end", f"· {kp}\n")
        detail.insert("end", "\n来源：", "label")
        detail.insert("end", str(url or "-"))
        state["current"] = card
        if url:
            url_btn.configure(state="normal",
                              command=lambda u=url: opener(u))
        else:
            url_btn.configure(state="disabled")

    def _pick(_ev=None):
        sel = lb.curselection()
        if not sel:
            return
        card = _shown[sel[0]]
        _render_detail(card)
        on_select(card)

    _shown = []

    def _refresh(_ev=None):
        choice = filter_var.get()
        if choice.startswith("装备:"):
            shown = filter_cards(cards, equipment=choice.split(":", 1)[1])
        elif choice == "全部":
            shown = list(cards)
        else:
            shown = filter_cards(cards, pattern=choice)
        _shown[:] = shown
        lb.delete(0, "end")
        for c in shown:
            lb.insert("end", card_title_line(c))

    cb.bind("<<ComboboxSelected>>", _refresh)
    lb.bind("<<ListboxSelect>>", _pick)
    _refresh()

    return {"frame": wrap, "listbox": lb, "detail": detail,
            "url_btn": url_btn, "filter": cb}


# ---------------- 赛前简报：解析 + 渲染 PNG ----------------

def render_brief_md(text):
    """把 brief.md 五段解析成 {sections:[{title, paragraphs:[{text, refs}]}], refs:[]}。

    `## 标题` 切段；段内 [k012] 形式引用被切进 refs，渲染时打青色标记。纯函数。
    """
    sections = []
    cur = None
    refs = []
    for raw in (text or "").splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "paragraphs": []}
            sections.append(cur)
            continue
        if not line.strip():
            continue
        if cur is None:
            cur = {"title": "", "paragraphs": []}
            sections.append(cur)
        found = REF_RE.findall(line)
        refs.extend(found)
        cur["paragraphs"].append({"text": line.strip(), "refs": found})
    seen, uniq = set(), []
    for r in refs:
        if r not in seen:
            seen.add(r)
            uniq.append(r)
    return {"sections": sections, "refs": uniq}


def _brief_font(size, bold=False):
    for name in ("msyhbd.ttc" if bold else "msyh.ttc",
                 "arialbd.ttf" if bold else "arial.ttf"):
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", name), size)
        except Exception:
            continue
    return ImageFont.load_default()


def export_brief_png(brief_struct, path, size=(900, 1200)):
    """把简报结构渲染成 1 页 PNG（深底、加粗段标题、[k012] 青色）。中文字体回退 YaHei→Arial→默认。"""
    W, H = size
    img = Image.new("RGB", (W, H), (11, 15, 18))
    d = ImageDraw.Draw(img)

    f_title = _brief_font(30, bold=True)
    f_head = _brief_font(18, bold=True)
    f_body = _brief_font(14)
    f_ref = _brief_font(13, bold=True)

    margin = 48
    y = 46
    d.text((margin, y), "赛前简报", font=f_title, fill=(238, 241, 244))
    y += 52

    refs = brief_struct.get("refs") or []
    if refs:
        d.text((margin, y), "参考：", font=f_body, fill=(148, 159, 168))
        rx = margin + d.textlength("参考：", font=f_body) + 6
        for r in refs:
            w = d.textlength(f"[{r}]", font=f_ref) + 16
            d.rounded_rectangle([rx, y - 2, rx + w, y + 22], radius=10,
                                fill=(24, 33, 40), outline=(94, 214, 214))
            d.text((rx + 8, y + 2), f"[{r}]", font=f_ref, fill=(94, 214, 214))
            rx += w + 10
        y += 40

    def _wrap_segments(segs, max_w):
        """segs: [(text, is_ref)]；按字符折行，引用不跨段拆开。返回 [[(text,is_ref)]]。"""
        lines, cur = [], []
        cur_w = 0.0
        for text, is_ref in segs:
            for ch in text:
                w = d.textlength(ch, font=(f_ref if is_ref else f_body))
                if cur_w + w > max_w and cur:
                    lines.append(cur)
                    cur, cur_w = [], 0.0
                cur.append((ch, is_ref))
                cur_w += w
        if cur:
            lines.append(cur)
        return lines

    for sec in brief_struct.get("sections") or []:
        if y > H - 120:
            break
        if sec.get("title"):
            d.text((margin, y), sec["title"], font=f_head, fill=(240, 196, 82))
            y += 30
        for para in sec.get("paragraphs") or []:
            # 把段落按引用切成段
            segs, last = [], 0
            for m in REF_RE.finditer(para["text"]):
                if m.start() > last:
                    segs.append((para["text"][last:m.start()], False))
                segs.append((m.group(0), True))
                last = m.end()
            if last < len(para["text"]):
                segs.append((para["text"][last:], False))
            for line in _wrap_segments(segs, W - 2 * margin):
                if y > H - 60:
                    break
                x = margin
                for ch, is_ref in line:
                    d.text((x, y), ch, font=(f_ref if is_ref else f_body),
                           fill=((94, 214, 214) if is_ref else (206, 212, 218)))
                    x += d.textlength(ch, font=(f_ref if is_ref else f_body))
                y += 24
            y += 8

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img.save(path)
    return path
