# -*- coding: utf-8 -*-
"""ClashLab 桌面客户端：单窗口，四页（实时 / 研究 / 采集 / 设置）。

原则：
- 界面只做"调度 + 展示"，采集与研究都在后台线程跑，主线程只刷 UI；
- 研究页直接复用 cli._sim_from_layout + study.build_study，保证 CLI 与 GUI 结果一致；
- 大模型复核只在用户点按钮时调用，且必须过 llm.validate_tactics，被拒绝就明确显示拒绝原因。
"""
import json
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from . import config as cfgmod, llm, paths, planner, prompts, ui
from . import ui_profile as uprof

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def res_path(*parts):
    """打包后从 _MEIPASS 读资源，源码运行时从工程根目录读（P0-04：锚项目根，不靠 CWD）。"""
    base = paths.resource_base()
    return os.path.join(base, *parts)


def out_path(*parts):
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = ROOT
    p = os.path.join(base, "out", *parts)
    os.makedirs(os.path.dirname(p) if os.path.splitext(p)[1] else p, exist_ok=True)
    return p


DARK_BG = "#0b0f12"
PANEL_BG = "#121820"
CARD_BG = "#161e26"
LINE = "#28333c"
INK = "#eef1f4"
GREY = "#94a0a8"
DIM = "#63707a"
CYAN = "#5ed6d6"
AMBER = "#f0c452"
CORAL = "#e87460"
GREEN = "#60c882"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ClashLab · 部落冲突战术研究台")
        self.root.geometry("1200x780")
        self.root.configure(bg=DARK_BG)
        self.root.minsize(1080, 700)

        self.cfg = self._load_cfg()
        self.logq = queue.Queue()
        self.monitor_stop = threading.Event()
        self.monitor_thread = None
        self.console = None
        self.last_report = None
        self.last_plans = None
        self.last_sim = None
        self.last_ring = None
        self.marks = None
        self._last_frame = None
        # 画像 / 卡库 / 赛前（UI 层持有，算法侧不读 self）
        self.profile = self._load_profile_local()
        self.cards = []
        self.cards_demo = False
        self.selected_card = None
        self.panel_footer = None
        self.pb = None
        self._profile_widgets = None

        self._build_style()
        self._build_layout()
        self._show_page("live")
        self._pump_log()
        self.root.after(400, self._pump_monitor)

    # ---------------- 配置 ----------------
    def _cfg_file(self):
        return os.path.join(ROOT, "config", "ui.json")

    def _load_cfg(self):
        d = {"serial": "127.0.0.1:5555", "adb": "", "model": "deepseek-v4.1-flash",
             "out": "out", "layout": os.path.join("layouts", "th13_sample.json")}
        try:
            with open(self._cfg_file(), "r", encoding="utf-8") as f:
                d.update(json.load(f))
        except Exception:
            pass
        if not d.get("adb"):
            d["adb"] = cfgmod.find_adb()
        return d

    def _save_cfg(self):
        try:
            os.makedirs(os.path.dirname(self._cfg_file()), exist_ok=True)
            with open(self._cfg_file(), "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=1)
        except Exception as e:
            self.log(f"[配置] 保存失败 {e}")

    # ---------------- 画像 / 卡库 / 赛前（UI 层持有，算法侧不读 self） ----------------
    def _load_profile_local(self):
        """优先 equipment 模块的画像 IO（算法侧契约一致），缺失回退 ui_profile。"""
        try:
            from . import equipment
            return equipment.load_profile(uprof.HEROES_JSON)
        except Exception:
            return uprof.load_profile(uprof.HEROES_JSON)

    def _save_profile_local(self):
        try:
            from . import equipment
            equipment.save_profile(self.profile, uprof.HEROES_JSON)
        except Exception:
            uprof.save_profile(self.profile, uprof.HEROES_JSON)

    @staticmethod
    def _normalize_index_row(r):
        """index.json 行（扁平索引）/ demo 卡 → 卡库区统一外形。"""
        src = r.get("source") or {}
        if isinstance(src, dict):
            url = src.get("url") or r.get("url", "") or ""
            name = src.get("name") or src.get("site") or r.get("site") or "?"
        else:
            url = r.get("url", "") or ""
            name = r.get("site") or src or "?"
        kp = r.get("key_points") or ([r["summary"]] if r.get("summary") else [])
        return {
            "id": r.get("id"),
            "title": r.get("title") or r.get("summary") or "未命名",
            "source": {"name": name, "url": url},
            "date": r.get("date") or "?",
            "confidence": r.get("confidence"),
            "pattern": r.get("pattern", ""),
            "equipment": r.get("equipment") or [],
            "key_points": kp,
        }

    def _load_cards(self):
        real = os.path.join(ROOT, "knowledge", "index.json")
        if os.path.exists(real):
            rows = uprof.load_cards(real)
            return [self._normalize_index_row(r) for r in rows], False
        return uprof.load_cards(uprof.INDEX_DEMO), True

    def _open_url(self, url):
        try:
            webbrowser.open(url)
        except Exception:
            pass

    def _on_card_select(self, card):
        self.selected_card = card
        self.log(f"[卡库] 选中 {card.get('id')} {str(card.get('title',''))[:40]}")

    @staticmethod
    def _read_json(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def _read_text(path):
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _load_prebattle(self):
        """读 out/prebattle；缺失退 info_demo.json / brief_demo.md 并标 demo。"""
        info_p = out_path("prebattle", "info.json")
        brief_p = out_path("prebattle", "brief.md")
        demo = not (os.path.exists(info_p) and os.path.exists(brief_p))
        if demo:
            info_p = os.path.join(ROOT, "out", "prebattle", "info_demo.json")
            brief_p = os.path.join(ROOT, "out", "prebattle", "brief_demo.md")
        return {"info": self._read_json(info_p) or {},
                "brief": self._read_text(brief_p),
                "demo": demo, "info_path": info_p, "brief_path": brief_p}

    def _assemble_footer(self, draw):
        """面板底部小字：画像行取自 self.profile；参考卡 id 优先 marks.cards，缺则卡库。"""
        seg = []
        line = uprof.profile_summary_line(self.profile)
        if line:
            seg.append("画像 " + line)
        refs = (draw or {}).get("cards") if isinstance(draw, dict) else None
        if refs:
            seg.append("参考 " + "".join(f"[{i}]" for i in refs))
        else:
            r = uprof.card_refs_line(self.cards)
            if r:
                seg.append("参考 " + r)
        return " | ".join(seg)

    def _refresh_used_missing(self, draw=None):
        """used/missing 优先 marks.profile（算法侧），缺则 UI 层对照卡库反推。"""
        used, missing = [], []
        prof = (draw or {}).get("profile") if isinstance(draw, dict) else None
        if isinstance(prof, dict):
            used = prof.get("used") or []
            missing = prof.get("missing") or []
        else:
            res = uprof.compute_used_missing(self.profile, cards=self.cards)
            used = [x["id"] for x in res["used"]]
            missing = [x["id"] for x in res["missing"]]
        used_txt = "、".join(uprof.equipment_label(i) for i in used) or "—"
        miss_txt = "、".join(uprof.equipment_label(i) for i in missing) or "无"
        if getattr(self, "lbl_used", None) is not None:
            self.lbl_used.configure(text=f"已具备 {used_txt}　|　缺失 {miss_txt}")

    # ---------------- 样式 ----------------
    def _build_style(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TFrame", background=DARK_BG)
        s.configure("Card.TFrame", background=CARD_BG, relief="flat")
        s.configure("TLabel", background=DARK_BG, foreground=INK, font=("Microsoft YaHei", 10))
        s.configure("Dim.TLabel", background=DARK_BG, foreground=DIM, font=("Microsoft YaHei", 9))
        s.configure("H1.TLabel", background=DARK_BG, foreground=INK, font=("Microsoft YaHei", 18, "bold"))
        s.configure("H2.TLabel", background=CARD_BG, foreground=INK, font=("Microsoft YaHei", 12, "bold"))
        s.configure("Card.TLabel", background=CARD_BG, foreground=GREY, font=("Microsoft YaHei", 9))
        s.configure("TButton", background=CARD_BG, foreground=INK, borderwidth=0,
                    font=("Microsoft YaHei", 10), padding=(12, 7))
        s.map("TButton", background=[("active", "#243039"), ("pressed", "#1a242c")])
        s.configure("Accent.TButton", background="#1f3f40", foreground=CYAN,
                    font=("Microsoft YaHei", 10, "bold"), padding=(14, 8))
        s.map("Accent.TButton", background=[("active", "#26504f")])
        s.configure("Nav.TButton", background=DARK_BG, foreground=GREY, anchor="w",
                    font=("Microsoft YaHei", 11), padding=(18, 12))
        s.map("Nav.TButton", background=[("active", "#151d24")])
        s.configure("TEntry", fieldbackground=CARD_BG, foreground=INK, insertcolor=INK,
                    borderwidth=0, padding=6)
        s.configure("TNotebook", background=DARK_BG, borderwidth=0)

    # ---------------- 布局 ----------------
    def _build_layout(self):
        left = tk.Frame(self.root, bg="#0e1318", width=210)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="CLASH LAB", bg="#0e1318", fg=CYAN,
                 font=("Microsoft YaHei", 16, "bold")).pack(anchor="w", padx=20, pady=(20, 2))
        tk.Label(left, text="战术研究台 v0.2", bg="#0e1318", fg=DIM,
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=20, pady=(0, 18))

        self.nav_buttons = {}
        for key, label in [("live", "实时"), ("study", "研究"), ("prebattle", "赛前"),
                           ("farm", "采集"), ("settings", "设置")]:
            b = ttk.Button(left, text=f"  {label}", style="Nav.TButton",
                           command=lambda k=key: self._show_page(k))
            b.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = b

        tk.Frame(left, bg="#0e1318").pack(fill="both", expand=True)
        self.lbl_status = tk.Label(left, text="● 未连接", bg="#0e1318", fg=DIM,
                                   font=("Microsoft YaHei", 9), anchor="w", justify="left")
        self.lbl_status.pack(anchor="w", padx=20, pady=(0, 18))

        self.right = tk.Frame(self.root, bg=DARK_BG)
        self.right.pack(side="left", fill="both", expand=True)
        self.pages = {}
        self._build_live()
        self._build_study()
        self._build_prebattle()
        self._build_farm()
        self._build_settings()

    def _card(self, parent, title=None):
        c = tk.Frame(parent, bg=CARD_BG, highlightbackground=LINE, highlightthickness=1)
        if title:
            tk.Label(c, text=title, bg=CARD_BG, fg=INK,
                     font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        return c

    def _show_page(self, key):
        for k, p in self.pages.items():
            p.pack_forget()
        self.pages[key].pack(fill="both", expand=True, padx=24, pady=18)
        for k, b in self.nav_buttons.items():
            b.configure(style="Nav.TButton")
        self.nav_buttons[key].configure(style="Accent.TButton")

    # ---------------- 页：实时 ----------------
    def _build_live(self):
        page = tk.Frame(self.right, bg=DARK_BG)
        self.pages["live"] = page
        tk.Label(page, text="实时战场", bg=DARK_BG, fg=INK,
                 font=("Microsoft YaHei", 18, "bold")).pack(anchor="w")
        tk.Label(page, text="ADB 只读采集 → 标定 → 叠加层。默认不点任何游戏内按钮。",
                 bg=DARK_BG, fg=DIM, font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(2, 14))

        top = self._card(page)
        top.pack(fill="x")
        row = tk.Frame(top, bg=CARD_BG)
        row.pack(fill="x", padx=16, pady=(14, 16))
        tk.Label(row, text="序列号", bg=CARD_BG, fg=GREY, font=("Microsoft YaHei", 9)).pack(side="left")
        self.e_serial = ttk.Entry(row, width=20)
        self.e_serial.insert(0, self.cfg["serial"])
        self.e_serial.pack(side="left", padx=(8, 14))
        ttk.Button(row, text="连接 / 体检", command=self._connect).pack(side="left", padx=4)
        ttk.Button(row, text="开始监视", style="Accent.TButton", command=self._start_monitor).pack(side="left", padx=4)
        ttk.Button(row, text="停止", command=self._stop_monitor).pack(side="left", padx=4)
        ttk.Button(row, text="弹出战术中枢", command=self._open_console).pack(side="left", padx=4)

        mid = tk.Frame(page, bg=DARK_BG)
        mid.pack(fill="both", expand=True, pady=12)

        leftbox = self._card(mid, "当前画面")
        leftbox.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.lbl_frame = tk.Label(leftbox, bg="#05080a", text="等待画面…", fg=DIM)
        self.lbl_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        rightbox = self._card(mid, "状态")
        rightbox.configure(width=330)
        rightbox.pack(side="left", fill="y")
        rightbox.pack_propagate(False)
        self.lbl_metrics = tk.Label(rightbox, text="状态  -\n标定  -\n帧率  -\n建筑  -",
                                    bg=CARD_BG, fg=INK, font=("Microsoft YaHei", 10),
                                    anchor="nw", justify="left")
        self.lbl_metrics.pack(fill="x", padx=16, pady=(8, 8))
        tk.Label(rightbox, text="日志", bg=CARD_BG, fg=DIM,
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=16)
        self.txt_log = tk.Text(rightbox, bg="#0b0f12", fg=GREY, bd=0, highlightthickness=0,
                              font=("Consolas", 9), wrap="word")
        self.txt_log.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def _connect(self):
        serial = self.e_serial.get().strip()
        self.cfg["serial"] = serial
        self._save_cfg()

        def work():
            try:
                from . import adb as adbmod
                a = adbmod.Adb(self.cfg.get("adb") or cfgmod.find_adb(), serial)
                a.ensure_device()
                size = a.wm_size()
                focus = a.current_focus()
                frame, ms, n = a.screencap()
                self.log(f"[体检] 设备 {a.serial}  分辨率 {size}  实际帧 {frame.shape[1]}x{frame.shape[0]}  "
                         f"{ms:.0f}ms  {n//1024}KB")
                self.log(f"[体检] 前台 {focus[:70]}")
                self._set_status(True, f"● 已连接 {a.serial}")
            except Exception as e:
                self.log(f"[体检] 失败 {e}")
                self._set_status(False, "● 连接失败")

        threading.Thread(target=work, daemon=True).start()

    def _start_monitor(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.log("[监视] 已在运行")
            return
        self.monitor_stop.clear()

        def loop():
            from . import adb as adbmod, farm
            try:
                a = adbmod.Adb(self.cfg.get("adb") or cfgmod.find_adb(), self.cfg["serial"])
                a.ensure_device()
            except Exception as e:
                self.log(f"[监视] 连接失败 {e}")
                self._set_status(False, "● ADB 未连接：检查模拟器与 adb 路径后重试")
                return
            while not self.monitor_stop.is_set():
                try:
                    frame, ms, _ = a.screencap()
                    state, detail = farm.probe_state(frame)
                    self.logq.put(("frame", (frame, state, detail, ms)))
                    self._set_status(True, f"● 已连接 · {state}")
                except Exception as e:
                    self.log(f"[监视] {e}")
                if self.monitor_stop.wait(0.6):
                    break

        self.monitor_thread = threading.Thread(target=loop, daemon=True)
        self.monitor_thread.start()
        self.log("[监视] 开始")

    def _stop_monitor(self):
        self.monitor_stop.set()
        self.log("[监视] 停止")

    def _open_console(self):
        if self.console is None:
            self.console = ui.TacticConsole(width=1280, height=720, overlay=False, panel=True,
                                            on_action=self._console_action)
            self.console.attach(self.root)
        if self.last_plans:
            self.console.update_state(info={"connected": True, "dash": {"ok": True, "state": "研究"}},
                                     report=self.last_report, plans=self.last_plans,
                                     footer=self.panel_footer)

    def _console_action(self, action):
        if action == "card:a":
            pass
        elif action.startswith("step:"):
            self.log(f"[执行顺序] 选中 {action}（高亮 2s）")
        elif action == "研究图":
            self._open_png(out_path("study", "study.png"))
        elif action == "重跑研究":
            self._run_study()
        elif action == "复制计划":
            if self.last_plans:
                txt = json.dumps(self.last_plans, ensure_ascii=False, indent=1)
                self.root.clipboard_clear()
                self.root.clipboard_append(txt)
                self.log("[剪贴板] 已复制候选方案 JSON")

    # ---------------- 页：研究 ----------------
    def _build_study(self):
        page = tk.Frame(self.right, bg=DARK_BG)
        self.pages["study"] = page
        tk.Label(page, text="赛前研究", bg=DARK_BG, fg=INK,
                 font=("Microsoft YaHei", 18, "bold")).pack(anchor="w")
        tk.Label(page, text="阵型 JSON → 覆盖/弱侧/入点/首打顺序 → 三面板研究图；模型只做复核，不进实时回路。",
                 bg=DARK_BG, fg=DIM, font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(2, 14))

        bar = tk.Frame(page, bg=DARK_BG)
        bar.pack(fill="x")
        tk.Label(bar, text="阵型", bg=DARK_BG, fg=GREY, font=("Microsoft YaHei", 9)).pack(side="left")
        self.e_layout = ttk.Entry(bar, width=48)
        self.e_layout.insert(0, self.cfg.get("layout", ""))
        self.e_layout.pack(side="left", padx=8)
        ttk.Button(bar, text="选择…", command=self._pick_layout).pack(side="left", padx=4)
        ttk.Button(bar, text="生成研究", style="Accent.TButton", command=self._run_study).pack(side="left", padx=4)
        ttk.Button(bar, text="大模型复核", command=self._run_review).pack(side="left", padx=4)
        ttk.Button(bar, text="生成标注", command=self._gen_marks).pack(side="left", padx=4)
        ttk.Button(bar, text="推送到HUD", command=self._push_marks_hud).pack(side="left", padx=4)
        ttk.Button(bar, text="导出标注图", command=self._export_marks).pack(side="left", padx=4)
        self.style_var = tk.StringVar(value="terse")
        self.cb_style = ttk.Combobox(bar, width=12, state="readonly",
                                     values=[v for _, v in prompts.style_names()])
        self.cb_style.set(prompts.get_style("terse")["label"])
        self.cb_style.pack(side="left", padx=(8, 4))
        self.cb_style.bind("<<ComboboxSelected>>", self._on_style)
        self.lbl_speed = tk.Label(bar, text="", bg=DARK_BG, fg=DIM, font=("Microsoft YaHei", 9))
        self.lbl_speed.pack(side="left", padx=6)
        ttk.Button(bar, text="打开研究图", command=lambda: self._open_png(out_path("study", "study.png"))).pack(side="left", padx=4)

        body = tk.Frame(page, bg=DARK_BG)
        body.pack(fill="both", expand=True, pady=12)
        self.lbl_study = tk.Label(body, bg="#05080a", text="尚未生成", fg=DIM)
        self.lbl_study.pack(side="left", fill="both", expand=True, padx=(0, 12))

        side = self._card(body, "模型复核")
        side.configure(width=340)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        self.txt_review = tk.Text(side, height=11, bg=CARD_BG, fg=GREY, bd=0, wrap="word",
                                  font=("Microsoft YaHei", 9), highlightthickness=0)
        self.txt_review.tag_configure("ref", foreground=CYAN)
        self.txt_review.tag_configure("head", foreground=AMBER)
        self.txt_review.pack(fill="x", padx=16, pady=(6, 10))
        self.txt_review.configure(state="disabled")
        tk.Label(side, text="首打顺序", bg=CARD_BG, fg=DIM, font=("Microsoft YaHei", 9)).pack(anchor="w", padx=16)
        self.lbl_prio = tk.Label(side, text="—", bg=CARD_BG, fg=INK, font=("Microsoft YaHei", 9),
                                 anchor="nw", justify="left", wraplength=300)
        self.lbl_prio.pack(fill="x", padx=16, pady=(2, 10))

        # ---- 参考打法（战术卡库）：index.json 缺失退 demo 并标"示例" ----
        self.cards, self.cards_demo = self._load_cards()
        cards_card = self._card(page, "参考打法（战术卡库）")
        cards_card.pack(fill="x", pady=(12, 0))
        if self.cards_demo:
            tk.Label(cards_card, text="示例数据：knowledge/index.json 未找到，使用 index_demo.json",
                     bg=CARD_BG, fg=AMBER, font=("Microsoft YaHei", 9)).pack(anchor="w", padx=16, pady=(8, 0))
        self.cards_widget = uprof.build_cards_widgets(
            cards_card, self.cards, self._on_card_select, open_url=self._open_url)
        self.cards_widget["frame"].pack(fill="x", padx=4, pady=4)

    # ---------------- 页：赛前 ----------------
    HERO_ICON = {"queen": "queen.png", "king": "king.png",
                 "warden": "warden.png", "rc": "rc.png"}

    def _pb_chip(self, parent, text, fg):
        tk.Label(parent, text=text, bg=CARD_BG, fg=fg, font=("Microsoft YaHei", 9),
                 padx=10, pady=4).pack(side="left", padx=(0, 8))

    def _pb_load_icon(self, path, size):
        try:
            from PIL import Image
            im = Image.open(path).convert("RGBA")
            im.thumbnail((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception:
            return None

    def _build_prebattle(self):
        page = tk.Frame(self.right, bg=DARK_BG)
        self.pages["prebattle"] = page
        tk.Label(page, text="赛前简报", bg=DARK_BG, fg=INK,
                 font=("Microsoft YaHei", 18, "bold")).pack(anchor="w")
        tk.Label(page, text="阵型/侦察已知信息 → 五段简报；未知项显式标珊瑚色，不隐藏。",
                 bg=DARK_BG, fg=DIM, font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(2, 14))

        self.pb = self._load_prebattle()
        self._pb_photos = []

        chips = tk.Frame(page, bg=DARK_BG)
        chips.pack(fill="x", pady=(4, 12))
        info = self.pb["info"] or {}
        dc = info.get("defense_counts") or {}
        chip_defs = [
            (f"TH {info.get('th') or '?'}", CYAN),
            (f"阵型 {info.get('layout_id') or '?'}", AMBER),
            (f"防御 {sum(int(v) for v in dc.values())} 座", INK),
            (f"覆盖 dps {info.get('core_cover_dps', '?')}", INK),
            (f"重心 {tuple(info.get('centroid') or [])}", INK),
        ]
        for txt, col in chip_defs:
            self._pb_chip(chips, txt, col)
        if self.pb["demo"]:
            self._pb_chip(chips, "示例", CORAL)

        body = tk.Frame(page, bg=DARK_BG)
        body.pack(fill="both", expand=True)
        left = self._card(body, "我方画像")
        left.pack(side="left", fill="y", padx=(0, 12))
        right = self._card(body, "简报")
        right.pack(side="left", fill="both", expand=True)
        self._pb_left, self._pb_right = left, right
        self._render_pb_left()
        self._render_pb_brief()

        btns = tk.Frame(page, bg=DARK_BG)
        btns.pack(fill="x", pady=(12, 0))
        ttk.Button(btns, text="重新生成简报", command=self._regen_brief).pack(side="left")
        ttk.Button(btns, text="按此简报出标注", style="Accent.TButton",
                   command=self._gen_marks).pack(side="left", padx=8)
        ttk.Button(btns, text="导出简报 PNG", command=self._export_brief_png).pack(side="left", padx=8)

    def _render_pb_left(self):
        left = self._pb_left
        for w in left.winfo_children()[1:]:
            w.destroy()
        info = self.pb["info"] or {}
        op = info.get("our_profile") or {}
        for role, (name, _lv) in uprof.HERO_META.items():
            row = tk.Frame(left, bg=CARD_BG)
            row.pack(fill="x", padx=16, pady=6)
            photo = self._pb_load_icon(
                res_path("assets", "coc", "heroes", self.HERO_ICON[role]), 40)
            if photo:
                lab = tk.Label(row, image=photo, bg=CARD_BG)
                lab.pack(side="left", padx=(0, 8))
                self._pb_photos.append(photo)
            else:
                tk.Label(row, text=name[0], bg="#22303a", fg=CYAN, width=3, height=2,
                         font=("Microsoft YaHei", 11, "bold")).pack(side="left", padx=(0, 8))
            tk.Label(row, text=name, bg=CARD_BG, fg=INK,
                     font=("Microsoft YaHei", 10, "bold")).pack(side="left")
            eq = op.get(role) or self.profile["heroes"].get(role, {}).get("equipment") or []
            for eid in eq:
                ephoto = self._pb_load_icon(
                    res_path("assets", "coc", "equipment", f"{eid}.png"), 28)
                if ephoto:
                    lab = tk.Label(row, image=ephoto, bg=CARD_BG)
                    lab.pack(side="left", padx=3)
                    self._pb_photos.append(ephoto)
                else:
                    tk.Label(row, text=uprof.equipment_label(eid), bg="#22303a", fg=INK,
                             font=("Microsoft YaHei", 8), padx=6).pack(side="left", padx=3)
        res = uprof.compute_used_missing(self.profile, cards=self.cards)
        miss = "、".join(x["label"] for x in res["missing"]) or "无明显缺失"
        tk.Label(left, text="缺失：" + miss, bg=CARD_BG, fg=CORAL, anchor="w", justify="left",
                 font=("Microsoft YaHei", 9), wraplength=300).pack(fill="x", padx=16, pady=(6, 10))
        unknown = info.get("unknown") or []
        if unknown:
            tk.Label(left, text="未知项", bg=CARD_BG, fg=DIM,
                     font=("Microsoft YaHei", 9, "bold")).pack(anchor="w", padx=16)
            for u in unknown:
                tk.Label(left, text=u, bg="#3a2222", fg=CORAL, font=("Microsoft YaHei", 8),
                         padx=8, pady=2).pack(anchor="w", padx=16, pady=2)

    def _render_pb_brief(self):
        right = self._pb_right
        for w in right.winfo_children()[1:]:
            w.destroy()
        wrap = tk.Frame(right, bg=CARD_BG)
        wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        bar = tk.Scrollbar(wrap, orient="vertical")
        bar.pack(side="right", fill="y")
        txt = tk.Text(wrap, bg=CARD_BG, fg=INK, bd=0, wrap="word",
                      font=("Microsoft YaHei", 10), yscrollcommand=bar.set,
                      highlightthickness=0)
        bar.configure(command=txt.yview)
        txt.pack(fill="both", expand=True)
        txt.tag_configure("ref", foreground=CYAN)
        txt.tag_configure("sec", foreground=AMBER)
        ref_re = re.compile(r"\[[A-Za-z]+\d+\]")
        for line in self.pb["brief"].splitlines():
            if not line.strip():
                continue
            if line.startswith("【"):
                txt.insert("end", line + "\n", "sec")
                continue
            pos = 0
            for m in ref_re.finditer(line):
                if m.start() > pos:
                    txt.insert("end", line[pos:m.start()])
                txt.insert("end", m.group(0), "ref")
                pos = m.end()
            if pos < len(line):
                txt.insert("end", line[pos:])
            txt.insert("end", "\n")
        txt.configure(state="disabled")

    def _regen_brief(self):
        try:
            from . import prebattle as pb_mod
            layout = self.e_layout.get().strip() or None
            info = pb_mod.collect_info(sim=self.last_sim, layout=layout,
                                        profile=self.profile)
            cards = []
            try:
                from . import knowledge
                cards = knowledge.retrieve(profile=self.profile, k=3)
            except Exception:
                cards = []
            text = pb_mod.brief(self.last_report, self.last_plans, info, cards=cards)
            info_out = {k: v for k, v in info.items() if not k.startswith("_")}
            with open(out_path("prebattle", "info.json"), "w", encoding="utf-8") as f:
                json.dump(info_out, f, ensure_ascii=False, indent=2)
            with open(out_path("prebattle", "brief.md"), "w", encoding="utf-8") as f:
                f.write(text + "\n")
            self.pb = self._load_prebattle()
            self._render_pb_left()
            self._render_pb_brief()
            self.log("[赛前] 简报已重新生成并落盘")
        except Exception as e:
            self.log(f"[赛前] 重新生成失败 {e}")
            messagebox.showwarning("简报生成", f"未能重新生成：{e}")

    def _export_brief_png(self):
        struct = uprof.render_brief_md(self.pb["brief"])
        out = out_path("prebattle", "brief.png")
        uprof.export_brief_png(struct, out)
        self.log(f"[赛前] 简报 PNG 已导出 {out}")
        self._open_png(out)

    def _pick_layout(self):
        p = filedialog.askopenfilename(initialdir=res_path("layouts"),
                                       filetypes=[("阵型 JSON", "*.json")])
        if p:
            self.e_layout.delete(0, "end")
            self.e_layout.insert(0, p)

    def _run_study(self):
        layout = self.e_layout.get().strip()
        if not layout:
            messagebox.showwarning("缺少阵型", "请先选择一个阵型 JSON")
            return
        # P0-04：相对阵型路径锚项目根解析，双击 exe / 任意 CWD 都能找到。
        layout, err = paths.resolve_layout(layout)
        if err:
            self.log(f"[研究] {err}")
            messagebox.showerror("找不到阵型", err)
            return
        self.log(f"[研究] 开始 {layout}")

        def work():
            try:
                from .cli import _sim_from_layout
                from . import analysis, study as study_mod
                sim, data = _sim_from_layout(layout)
                army = dict(planner.DEFAULT_ARMY)
                ring = analysis.deployment_ring(sim)
                report, plans, fig = study_mod.build_study(sim, army, ring, out_dir=out_path("study"))
                # 线程内局部变量先落定，再一次性写实例属性（避免跨线程半赋值）
                self.last_sim, self.last_ring = sim, ring
                self.last_report, self.last_plans = report, plans
                payload = {"layout": os.path.basename(layout), "army": army,
                           "report": report, "plans": plans}
                with open(out_path("study", "study.json"), "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=1)
                self.logq.put(("study", (fig, report, plans)))
                self.log(f"[研究] 完成：{len(sim.buildings)} 建筑，最优入点 "
                         f"{report['sectors'][0]['tile'] if report['sectors'] else '-'}")
            except Exception as e:
                self.log(f"[研究] 失败 {e}")
                self.logq.put(("error", str(e)))

        threading.Thread(target=work, daemon=True).start()

    def _on_style(self, _e=None):
        label = self.cb_style.get()
        for k, v in prompts.style_names():
            if v == label:
                self.style_var.set(k)
                break
        self.log(f"[复核] 样式切到 {label}（max_tokens={prompts.get_style(self.style_var.get())['max_tokens']}）")

    def _run_review(self):
        if not self.last_plans:
            messagebox.showinfo("先跑研究", "请先生成研究图，再让模型复核")
            return
        layout_name = os.path.basename(self.e_layout.get().strip())
        style = self.style_var.get()
        # P0-06：缓存键带 army/profile/prebattle/report 指纹，换配置不命中旧条目。
        fp = prompts.fingerprint({"army": dict(planner.DEFAULT_ARMY),
                                  "profile": self.profile, "prebattle": self.pb,
                                  "report": self.last_report})
        hit = prompts.cache_get(layout_name, self.last_plans, style, extra_fp=fp)
        if hit:
            # 缓存命中：直接展示缓存结果，不重复调用模型，速度标签标缓存命中。
            self.logq.put(("review", (hit.get("status", "ok"), hit.get("model", "cache"),
                                     hit.get("summary", ""), hit.get("issues", []),
                                     hit.get("clean"))))
            self.lbl_speed.configure(text="缓存命中 0.0s")
            self.log("[复核] 命中本地缓存，未重复调用模型")
            return
        self.log(f"[复核] 调用大模型（样式 {style}）…")

        def work():
            t0 = time.time()
            try:
                ring = None
                try:
                    import numpy as np
                    from .cli import _sim_from_layout
                    from . import analysis
                    sim, _ = _sim_from_layout(self.e_layout.get().strip())
                    xs, ys = np.where(analysis.deployment_ring(sim))
                    ring = list(zip(xs.tolist(), ys.tolist()))
                except Exception as e:
                    self.log(f"[复核] 撒兵区计算失败，跳过越界校验 {e}")
                    ring = None
                brief = prompts.compact_brief(layout_name, self.last_report, self.last_plans,
                                              dict(planner.DEFAULT_ARMY))
                msgs, st = prompts.build_review_messages(brief, style)
                obj, used, raw = llm.chat_json(msgs, max_tokens=st["max_tokens"],
                                               temperature=0.1, retries=0)
                clean, issues = llm.validate_tactics(obj, ring_tiles=ring, max_entries=2)
                # P0-02：[soft] 只是局部条目告警，不阻断整条结论；只有 [hard] 才 rejected。
                status = "rejected" if llm.is_hard_rejection(issues) else "ok"
                summary = (clean or {}).get("verdict") or raw[:160]
                elapsed = round(time.time() - t0, 1)
                prompts.cache_put(layout_name, self.last_plans, style,
                                  {"status": status, "model": used, "summary": summary,
                                   "issues": issues, "clean": clean},
                                  extra_fp=fp)
                self.logq.put(("review", (status, used, summary, issues, clean)))
                self.log(f"[复核] {used} {elapsed}s 输入 {len(brief)} 字 -> {status}"
                         + ("" if not issues else "：" + "; ".join(issues)))
                self.logq.put(("speed", f"{elapsed}s · 输入 {len(brief)} 字 · {st['max_tokens']} tok"))
            except Exception as e:
                self.logq.put(("review", ("error", "-", str(e)[:200], [], None)))
                self.log(f"[复核] 失败 {e}")

        threading.Thread(target=work, daemon=True).start()

    # ---------------- 坐标标注（draw_calls 契约） ----------------
    MARKS_QUAD = [[697, 107], [944, 351], [672, 585], [347, 327]]

    def _demo_marks(self):
        """算法侧 plan_marks 未就绪时的契约示例数据（6 marks / 1 穿云箭 / 5 pins / 6 steps）。"""
        return {
            "version": 1,
            "marks": [
                {"kind": "building", "tile": [22, 12], "label": "防空", "role": "target", "seq": 1},
                {"kind": "building", "tile": [12, 22], "label": "防空", "role": "target", "seq": 2},
                {"kind": "building", "tile": [32, 32], "label": "散射炮", "role": "snipe", "seq": 3},
                {"kind": "building", "tile": [30, 14], "label": "鹰火炮", "role": "snipe", "seq": 4},
                {"kind": "building", "tile": [32, 22], "label": "防空", "role": "target", "seq": 5},
                {"kind": "building", "tile": [1, 22], "label": "贴边盲区", "role": "avoid", "seq": 6},
            ],
            "lines": [
                {"kind": "giant_arrow", "from": [8, 16], "to": [30, 14],
                 "hits": [[22, 12], [12, 22]], "label": "穿云箭 · 穿2防空"},
            ],
            "pins": [
                {"kind": "hero", "role": "queen", "tile": [8, 16], "order": 1, "label": "女王站位"},
                {"kind": "hero", "role": "king", "tile": [16, 20], "order": 2, "label": "国王"},
                {"kind": "hero", "role": "warden", "tile": [6, 24], "order": 3, "label": "守护者"},
                {"kind": "hero", "role": "rc", "tile": [14, 26], "order": 4, "label": "战宠"},
                {"kind": "troop", "role": "edrag", "tile": [10, 18], "count": 7,
                 "order": 5, "label": "雷龙×7"},
            ],
            "circles": [
                {"kind": "freeze", "tile": [22, 22], "radius": 4},
            ],
            "steps": [
                {"order": 1, "text": "女王(8,16) → (30,14) 穿2防空"},
                {"order": 2, "text": "国王跟进清边"},
                {"order": 3, "text": "守护者接战覆盖"},
                {"order": 4, "text": "战宠掩护女王"},
                {"order": 5, "text": "雷龙×7 主力进场"},
                {"order": 6, "text": "冰冻金身保主力"},
            ],
        }

    def _retrieve_cards_for_marks(self):
        try:
            from . import knowledge
            return knowledge.retrieve(profile=self.profile, k=3) or []
        except Exception as e:
            self.log(f"[卡库] 检索失败 {e}")
            return []

    def _prebattle_for_marks(self):
        info_p = out_path("prebattle", "info.json")
        if not os.path.exists(info_p):
            return None
        info = self._read_json(info_p) or {}
        brief_p = out_path("prebattle", "brief.md")
        info["brief_chars"] = len(self._read_text(brief_p)) if os.path.exists(brief_p) else 0
        return info

    def _gen_marks(self):
        """生成 draw_calls：优先算法侧 plan_marks.build_marks，未跑过研究则提示。"""
        if self.last_sim is None or self.last_ring is None or not self.last_plans:
            messagebox.showinfo("先跑研究", "请先生成研究，再生成标注")
            return
        draw = None
        try:
            from . import plan_marks
            try:
                draw = plan_marks.build_marks(
                    self.last_sim, self.last_ring, self.last_report, self.last_plans,
                    dict(planner.DEFAULT_ARMY),
                    profile=self.profile,
                    cards=self._retrieve_cards_for_marks(),
                    prebattle=self._prebattle_for_marks())
                self.log("[标注] 算法侧 plan_marks.build_marks 生成成功（含画像/卡库/赛前）")
            except TypeError as e:
                # 旧签名无 profile=/cards=/prebattle=：退回位置调用，不改坏主干
                self.log(f"[标注] build_marks 签名不支持扩展参数（{e}），退回旧调用")
                draw = plan_marks.build_marks(self.last_sim, self.last_ring, self.last_report,
                                              self.last_plans, dict(planner.DEFAULT_ARMY))
        except Exception as e:
            self.log(f"[标注] plan_marks 生成失败（{type(e).__name__}: {e}），载入 demo 标注数据")
            draw = self._demo_marks()
        self.marks = draw
        self.panel_footer = self._assemble_footer(draw)
        self._refresh_used_missing(draw)
        try:
            os.makedirs(out_path("marks"), exist_ok=True)
            with open(out_path("marks", "marks.json"), "w", encoding="utf-8") as f:
                json.dump(draw, f, ensure_ascii=False, indent=1)
            self.log("[标注] draw_calls 已写 out/marks/marks.json")
        except Exception as e:
            self.log(f"[标注] 写 marks.json 失败 {e}")
        self._render_marks_preview()
        if self.console:
            self.console.update_state(marks=self.marks, footer=self.panel_footer)

    def _push_marks_hud(self):
        if not self.marks:
            messagebox.showinfo("先生成标注", "请先点「生成标注」")
            return
        if self.console:
            self.console.update_state(marks=self.marks, footer=self.panel_footer)
            self.log("[标注] 已推送到战术中枢 HUD")
        else:
            self.log("[标注] 战术中枢未打开，下次弹出后自动带上标注")

    def _export_marks(self):
        if not self.marks:
            messagebox.showinfo("先生成标注", "请先点「生成标注」")
            return
        base = filedialog.askopenfilename(
            title="选择标注底图",
            initialdir=os.path.dirname(out_path("live_00.png")),
            filetypes=[("图片", "*.png *.jpg *.jpeg")]) or out_path("live_00.png")
        self._render_marks_preview(base=base, save=out_path("ui", "marks_export.png"))
        self.log("[标注] 标注图已导出 out/ui/marks_export.png")

    def _render_marks_preview(self, base=None, save=None):
        """把 draw_calls 画到底图上并导出预览（Calib 走实测 quad）。"""
        from .geo import Calib
        from PIL import Image, ImageDraw
        base = base or out_path("live_00.png")
        calib = Calib.from_quad(self.MARKS_QUAD)
        bg = Image.open(base).convert("RGBA")
        layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ui.render_marks(d, calib, self.marks, t=0.0)
        out = Image.alpha_composite(bg, layer).convert("RGB")
        save = save or out_path("ui", "marks_preview.png")
        out.save(save)
        self.log(f"[标注] 预览已导出 {save}")

    # ---------------- 页：采集 ----------------
    def _build_farm(self):
        page = tk.Frame(self.right, bg=DARK_BG)
        self.pages["farm"] = page
        tk.Label(page, text="打鱼采集", bg=DARK_BG, fg=INK,
                 font=("Microsoft YaHei", 18, "bold")).pack(anchor="w")
        tk.Label(page, text="侦察截图入库，不进攻、不消耗奖杯；模型给阵型打标签，失败样本会被标成待人工确认。",
                 bg=DARK_BG, fg=DIM, font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(2, 14))

        bar = tk.Frame(page, bg=DARK_BG)
        bar.pack(fill="x")
        ttk.Button(bar, text="跑一轮采集", style="Accent.TButton", command=lambda: self._run_farm(1)).pack(side="left")
        ttk.Button(bar, text="连续 10 轮", command=lambda: self._run_farm(10)).pack(side="left", padx=6)
        ttk.Button(bar, text="打开样本目录", command=lambda: self._open_dir(out_path("farm"))).pack(side="left", padx=6)
        self.lbl_farm = tk.Label(bar, text="样本 0", bg=DARK_BG, fg=GREY, font=("Microsoft YaHei", 9))
        self.lbl_farm.pack(side="left", padx=16)
        tk.Label(bar, text="注意：真实账号自动化可能触发 Supercell 封禁，配置好样本源再用。",
                 bg=DARK_BG, fg=CORAL, font=("Microsoft YaHei", 9)).pack(side="right")

        self.gallery = self._card(page, "最近样本")
        self.gallery.pack(fill="both", expand=True, pady=12)

    def _run_farm(self, rounds):
        """跑采集轮次。

        live（是否真实下发点击）取值优先级：
        1. 配置文件 config/ui.json 的 ``farm_live`` 字段（或环境写入的同名字段）；
        2. 缺省 False —— 默认 dry-run，只记录不点击，真实下发必须显式开启并二次确认。
        use_llm 仍为 True（只打标签，不触设备）。
        """
        # P0-03：删除硬编码 live=True；默认 dry-run，真实下发需配置 farm_live=true 且弹窗确认。
        live = bool(self.cfg.get("farm_live", False))
        if live:
            if not messagebox.askyesno(
                    "真实下发确认",
                    "farm_live 已开启：即将向真实账号下发点击（不可撤销）。\n继续？"):
                self.log("[采集] 已取消：用户未确认真实下发，本轮保持 dry-run")
                return
        self.log(f"[采集] 启动 {rounds} 轮（live={live}，{'真实下发' if live else 'dry-run 不点'}）")

        def work():
            try:
                from .farm import Farm
                f = Farm(serial=self.cfg["serial"], out=out_path("farm"), mode="sample",
                         live=live, use_llm=True, logger=self.log)
                stats = f.run(rounds=rounds)
                self.logq.put(("farm", stats))
            except Exception as e:
                self.log(f"[采集] 失败 {e}")

        threading.Thread(target=work, daemon=True).start()

    # ---------------- 页：设置 ----------------
    def _build_settings(self):
        page = tk.Frame(self.right, bg=DARK_BG)
        self.pages["settings"] = page
        tk.Label(page, text="设置", bg=DARK_BG, fg=INK,
                 font=("Microsoft YaHei", 18, "bold")).pack(anchor="w")
        tk.Label(page, text="ADB、序列号、模型与输出目录；模型默认走 AstrBot 的 openai_1 provider。",
                 bg=DARK_BG, fg=DIM, font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(2, 14))

        # 内容超出窗口时纵向滚动（画像图标网格较高）
        canvas = tk.Canvas(page, bg=DARK_BG, highlightthickness=0)
        sb = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas, bg=DARK_BG)
        canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        card = self._card(body)
        card.pack(fill="x")
        rows = [("ADB 路径", "adb"), ("序列号", "serial"), ("模型", "model"), ("输出目录", "out")]
        self.e_cfg = {}
        for i, (label, key) in enumerate(rows):
            tk.Label(card, text=label, bg=CARD_BG, fg=GREY, font=("Microsoft YaHei", 9)).grid(
                row=i, column=0, sticky="w", padx=16, pady=8)
            e = ttk.Entry(card)
            e.insert(0, str(self.cfg.get(key, "")))
            e.grid(row=i, column=1, sticky="we", padx=8, pady=8)
            self.e_cfg[key] = e
        card.grid_columnconfigure(1, weight=1)

        btns = tk.Frame(card, bg=CARD_BG)
        btns.grid(row=len(rows), column=0, columnspan=2, sticky="e", padx=16, pady=(0, 14))
        ttk.Button(btns, text="保存", style="Accent.TButton", command=self._save_settings).pack(side="left")
        ttk.Button(btns, text="测试模型", command=self._test_model).pack(side="left", padx=8)

        # ---- 英雄装备画像（图标网格；保存 config/heroes.json；应用画像重算标注） ----
        pcard = self._card(body, "英雄装备画像")
        pcard.pack(fill="x", pady=12)

        def _prof_changed(role, level, equipment):
            self.profile["heroes"][role]["level"] = level
            self.profile["heroes"][role]["equipment"] = equipment
            self._refresh_used_missing()

        pouter, self._profile_widgets = uprof.build_profile_widgets(
            pcard, self.profile, _prof_changed)
        pouter.pack(fill="x", padx=4)

        pbtns = tk.Frame(pcard, bg=CARD_BG)
        pbtns.pack(fill="x", padx=16, pady=(4, 6))
        ttk.Button(pbtns, text="保存画像", style="Accent.TButton",
                   command=self._save_profile_btn).pack(side="left")
        ttk.Button(pbtns, text="应用画像（重算标注）",
                   command=self._apply_profile).pack(side="left", padx=8)
        ttk.Button(pbtns, text="从截图识别装备",
                   command=self._detect_equipment).pack(side="left", padx=8)

        self.lbl_used = tk.Label(pcard, text="", bg=CARD_BG, fg=GREEN, anchor="w",
                                 justify="left", font=("Microsoft YaHei", 9), wraplength=820)
        self.lbl_used.pack(fill="x", padx=16, pady=(2, 4))
        self.lbl_detect = tk.Label(pcard, text="视觉识别：取英雄界面截图做模板匹配，<0.7 标黄待确认，不自动写入。",
                                   bg=CARD_BG, fg=DIM, anchor="w", justify="left",
                                   font=("Microsoft YaHei", 9), wraplength=820)
        self.lbl_detect.pack(fill="x", padx=16, pady=(0, 12))
        self._refresh_used_missing()

        info = self._card(body, "环境")
        info.pack(fill="x", pady=12)
        tk.Label(info, text=f"Python  {sys.version.split()[0]}\n打包模式  {'EXE' if getattr(sys, 'frozen', False) else '源码'}\n"
                            f"资源目录  {getattr(sys, '_MEIPASS', ROOT)}",
                 bg=CARD_BG, fg=GREY, justify="left", anchor="w",
                 font=("Consolas", 9)).pack(fill="x", padx=16, pady=(0, 12))

    def _save_settings(self):
        for k, e in self.e_cfg.items():
            self.cfg[k] = e.get().strip()
        self._save_cfg()
        self.log("[设置] 已保存")
        messagebox.showinfo("已保存", "配置已写入 config/ui.json")

    def _test_model(self):
        def work():
            ok, model, ms, msg = llm.ping()
            self.log(f"[模型] {model or '-'} {ms}s {'ok' if ok else 'fail'} {msg}")
        threading.Thread(target=work, daemon=True).start()

    # ---- 画像保存 / 应用 / 截图识别 ----
    def _save_profile_btn(self):
        self._save_profile_local()
        self._refresh_used_missing()
        self.log("[画像] 已保存 config/heroes.json")
        messagebox.showinfo("已保存", "画像已写入 config/heroes.json")

    def _apply_profile(self):
        self._save_profile_local()
        self._refresh_used_missing()
        self.log("[画像] 应用画像，重算标注")
        self._gen_marks()

    def _detect_equipment(self):
        try:
            from . import equipment
            fn = getattr(equipment, "detect_equipment", None)
        except ImportError:
            fn = None
        if fn is None:
            self.lbl_detect.configure(text="视觉识别未就绪，请手动选择装备", fg=DIM)
            self.log("[识别] equipment.detect_equipment 不可用，跳过")
            return

        frame = self._last_frame
        if frame is None:
            path = filedialog.askopenfilename(title="选择英雄界面截图",
                                              filetypes=[("图片", "*.png *.jpg *.jpeg")])
            if not path:
                return

        def work():
            try:
                f = frame
                if f is None:
                    import cv2
                    f = cv2.imread(path)
                res = fn(f)
            except Exception as e:
                res = {"available": False, "reason": f"{type(e).__name__}: {e}",
                       "candidates": [], "pending": True}
            self.logq.put(("detect", res))

        threading.Thread(target=work, daemon=True).start()

    def _show_detect(self, res):
        if not res.get("available"):
            self.lbl_detect.configure(text="视觉识别不可用：" + str(res.get("reason", "")),
                                      fg=DIM)
            return
        tagged = uprof.tag_low_confidence(res.get("candidates") or [])
        parts = []
        for c in tagged:
            tag = "待确认" if c["tag"] == "待确认" else "可用候选"
            parts.append(f"{uprof.equipment_label(c['id'])}({c['id']}) {c['score']:.2f} {tag}")
        self.lbl_detect.configure(
            text="候选仅供参考，需手动勾选，不自动写入：" + "；".join(parts),
            fg=AMBER if res.get("pending") else GREEN)
        self.log("[识别] 候选：" + "；".join(parts))

    # ---------------- 工具 ----------------
    def log(self, s):
        self.logq.put(("log", s))

    def _set_status(self, ok, text):
        self.logq.put(("status", (ok, text)))

    def _open_png(self, path):
        if not os.path.exists(path):
            messagebox.showinfo("还没有图", f"请先跑一次研究\n{path}")
            return
        try:
            os.startfile(path)
        except Exception:
            pass

    def _open_dir(self, path):
        os.makedirs(path, exist_ok=True)
        try:
            os.startfile(path)
        except Exception:
            pass

    def _pump_log(self):
        try:
            while True:
                kind, payload = self.logq.get_nowait()
                if kind == "log":
                    self.txt_log.insert("end", payload + "\n")
                    self.txt_log.see("end")
                elif kind == "status":
                    ok, text = payload
                    self.lbl_status.configure(text=text, fg=GREEN if ok else CORAL)
                elif kind == "study":
                    self._show_study(*payload)
                elif kind == "frame":
                    self._show_frame(*payload)
                elif kind == "review":
                    self._show_review(*payload)
                elif kind == "speed":
                    self.lbl_speed.configure(text=payload)
                elif kind == "detect":
                    self._show_detect(payload)
                elif kind == "farm":
                    self.lbl_farm.configure(text=f"样本 {payload.get('scouted', 0)}  "
                                                 f"恢复弹窗 {payload.get('dialog_recovered', 0)}")
                elif kind == "error":
                    self.log("错误：" + payload)
        except queue.Empty:
            pass
        self.root.after(120, self._pump_log)

    def _show_frame(self, frame, state, detail, ms):
        self._last_frame = frame
        img = Image.fromarray(frame[:, :, ::-1])
        w = max(360, self.lbl_frame.winfo_width() - 20)
        img = img.resize((w, int(img.height * w / img.width)))
        photo = ImageTk.PhotoImage(img)
        self.lbl_frame.configure(image=photo, text="")
        self.lbl_frame.image = photo
        conf = (detail or {}).get("confidence") if isinstance(detail, dict) else None
        self.lbl_metrics.configure(
            text=f"状态  {state}\n标定  {(detail or {}).get('source', '-') if isinstance(detail, dict) else '-'}\n"
                 f"帧耗时  {ms:.0f} ms\n置信度  {conf if conf is not None else '-'}")
        if self.console and self.last_plans:
            self.console.update_state(info={"connected": True,
                                            "dash": {"ok": True, "state": state,
                                                     "detail": f"{ms:.0f}ms", "conf": conf,
                                                     "fps": 1000.0 / max(ms, 1)},
                                            "boundary": detail if isinstance(detail, dict) else {},
                                            "heat": None, "layout": None},
                                      report=self.last_report, plans=self.last_plans)

    def _show_study(self, fig, report, plans):
        img = Image.open(fig)
        w = max(480, self.lbl_study.winfo_width() - 16)
        img = img.resize((w, int(img.height * w / img.width)))
        photo = ImageTk.PhotoImage(img)
        self.lbl_study.configure(image=photo, text="")
        self.lbl_study.image = photo
        pri = report.get("priority") or []
        self.lbl_prio.configure(text="\n".join(
            f"{i+1}. {p['type']} ({p['tile'][0]},{p['tile'][1]})" for i, p in enumerate(pri[:5])) or "—")

    def _show_review(self, status, model, summary, issues, clean):
        head = {"ok": "已通过校验", "rejected": "被校验拒绝", "error": "调用失败"}.get(status, status)
        lines = [("head", f"{head} · {model}"), ("", "")]
        cards = prompts.to_cards(clean) if clean else []
        if cards:
            for c in cards:
                k = c["kind"]
                if k == "verdict":
                    lines.append(("", "结论  " + c["text"]))
                elif k == "confidence":
                    bar = "█" * max(1, int(round(c["value"] * 10))) + "░" * (10 - max(1, int(round(c["value"] * 10))))
                    lines.append(("", f"把握  {bar} {c['value']:.2f}"))
                elif k == "adjust":
                    t = c.get("tile") or ["?", "?"]
                    lines.append(("", f"改点  {c['id']} → ({t[0]},{t[1]})  {c['text']}"))
                elif k == "order":
                    lines.append(("", "首打  " + " → ".join(c["items"][:4])))
                elif k == "risk":
                    lines.append(("", "风险  " + "；".join(c["items"][:3])))
                elif k == "note":
                    lines.append(("", "补充  " + c["text"]))
        else:
            lines.append(("", summary))
        if issues:
            lines.append(("", ""))
            lines += [("", "校验问题：")] + [("", "· " + i) for i in issues[:5]]

        self.txt_review.configure(state="normal")
        self.txt_review.delete("1.0", "end")
        ref_re = re.compile(r"\[[A-Za-z]+\d+\]")
        for tag, text in lines:
            pos = 0
            for m in ref_re.finditer(text):
                if m.start() > pos:
                    self.txt_review.insert("end", text[pos:m.start()])
                self.txt_review.insert("end", m.group(0), "ref")
                pos = m.end()
            if pos < len(text):
                self.txt_review.insert("end", text[pos:])
            self.txt_review.insert("end", "\n")
        self.txt_review.tag_add("head", "1.0", "1.end")
        self.txt_review.configure(state="disabled")

    def _pump_monitor(self):
        self.root.after(400, self._pump_monitor)

    def run(self):
        self.root.mainloop()


def main():
    App().run()
    return 0


if __name__ == "__main__":
    main()
