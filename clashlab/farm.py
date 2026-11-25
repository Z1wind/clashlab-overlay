# -*- coding: utf-8 -*-
"""打鱼采样本引擎（半自动，默认不进攻）。

流程（sample 模式，只侦察不撒兵）：
  主页 -> 战斗 -> （联机菜单/开始进攻面板）-> 搜索 -> 侦察界面截图入库 -> 返回 -> 循环。
attack 模式仅在测试号上由规则/大模型给入点后真撒兵，本交付不启用。

红线：
  * 绝不点“进攻！/进攻”按钮，绝不撒兵；误入战斗界面立即返回/退出。
  * 每次真实 tap 前先截图，tap 后 >=1s 再截图；禁止盲点连点。
  * 默认 dry-run（不加 --live 不真点）。

合规说明：联网账号上的自动化按 Supercell 政策属于作弊，可能永久封禁。
本模块默认 sample 模式并不触碰战斗，建议只在测试号上使用 attack。
"""
import json
import os
import time

import cv2
import numpy as np

from . import adb as adbmod, config, vision

try:  # llm.py 可能被别的智能体并行编辑，导入失败不应让整个农场崩掉
    from . import llm
except Exception:  # pragma: no cover
    llm = None

# 已知持久阻塞（与本轮实探无关的环境/规则限制，每次报告都带出）
PERSISTENT_BLOCKERS = [
    "夜世界 0/9 兵、兵营 0/3 未建造，“立即寻找”被拦截；编辑军队只打开编成编辑器不训练，需人工先建兵营",
    "主村联机搜索被开战确认门挡住，红线禁止点“进攻！”，未进入匹配/侦察视图",
    "侦察界面 scout_back/scout_attack 候选坐标未实测，落样本前需前-后截图固化",
]

# 默认锚点（1280x720 输入坐标）。confirmed=False 的是待实测候选，不许当已确认用。
DEFAULT_ANCHORS = {
    # 建筑大师基地（夜世界）开始进攻链路
    "battle": {"point": [88, 645], "confirmed": True,
               "note": "主页左下“战斗”按钮（夜世界），home->开始进攻面板",
               "evidence": ["out/farm/probe/02_battle_open_before.png",
                            "out/farm/probe/03_battle_open_after.png"]},
    "attack_close": {"point": [1088, 133], "confirmed": True,
                      "note": "开始进攻面板右上红色关闭X，attack_menu->home 实测通过",
                      "evidence": ["out/farm/probe/73_attack_close_before.png",
                                   "out/farm/probe/74_attack_close_after.png"]},
    "find": {"point": [951, 474], "confirmed": True,
             "note": "开始进攻面板右下绿色“立即寻找！”按钮；0 兵时点了不进搜索（被拦截），按钮位置已确认",
             "evidence": ["out/farm/probe/05_find_crop.png"]},
    "edit_army": {"point": [421, 570], "confirmed": True,
                   "note": "开始进攻面板左下绿色“编辑军队”按钮，打开“选择军队”编成编辑器（不训练部队）",
                   "evidence": ["out/farm/probe/07_edit_army_before.png",
                                "out/farm/probe/08_edit_army_after.png"]},
    # 主村（家乡）联机链路
    "m_battle": {"point": [75, 635], "confirmed": True,
                 "note": "主村左下“战斗”按钮，主页->主村战斗菜单（联机/单人/练习）",
                 "evidence": ["out/farm/probe/45_mhome_battle2_before.png",
                              "out/farm/probe/46_mhome_battle2_after.png"]},
    "m_search": {"point": [197, 535], "confirmed": True,
                 "note": "主村常规战卡片“搜索对手 1500”按钮，点击->我的军队开战确认面板",
                 "evidence": ["out/farm/probe/55_search3_before.png",
                              "out/farm/probe/56_search3_after.png"]},
    "confirm_close": {"point": [1237, 90], "confirmed": True,
                       "note": "我的军队开战确认面板右上关闭X，实测关闭回主页（不点进攻！）",
                       "evidence": ["out/farm/probe/56_search3_after.png",
                                    "out/farm/probe/77_state.png"]},
    # 侦察界面（候选，未实测）
    "scout_back": {"point": [64, 44], "confirmed": False,
                   "note": "侦察界面左上返回（候选坐标，未实测）", "evidence": []},
    "scout_attack": {"point": [1150, 640], "confirmed": False,
                     "note": "侦察界面右下红色进攻（候选坐标，未实测；红线禁止点）",
                     "evidence": []},
}


def load_anchors(path="config/anchors.json"):
    """读取锚点。文件缺失/损坏都回落到 DEFAULT_ANCHORS，Farm 照样能跑。

    返回 {key: {"point":[x,y], "confirmed":bool, "note":..., "evidence":[...]}}。
    兼容旧格式：条目若是 [x,y] 列表，自动包成 dict。
    """
    out = {k: dict(v) for k, v in DEFAULT_ANCHORS.items()}
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, (list, tuple)):
                        out[k] = {"point": [int(v[0]), int(v[1])], "confirmed": False}
                    elif isinstance(v, dict):
                        merged = dict(out.get(k, {}))
                        merged.update(v)
                        if "point" in v:
                            merged["point"] = [int(v["point"][0]), int(v["point"][1])]
                        out[k] = merged
        except Exception as e:
            print(f"[farm] anchors.json 读取失败，使用默认: {e}")
    return out


def anchor_xy(anchors, key):
    """取运行时坐标 [x,y]。"""
    v = anchors.get(key)
    if isinstance(v, dict):
        return v["point"]
    return v


# ---------------- 界面识别 ----------------

def _region(frame, r):
    h, w = frame.shape[:2]
    x0, y0, x1, y1 = [int(v * (w if i % 2 == 0 else h)) for i, v in enumerate(r)]
    return frame[y0:y1, x0:x1]


def _ratio_in_hsv(patch, lo, hi):
    if patch.size == 0:
        return 0.0
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, np.array(lo), np.array(hi))
    return float((m > 0).mean())


def probe_state(frame):
    """返回 (state, detail)。

    状态：dialog / attack_menu(夜世界开始进攻面板) / battle_menu(主村联机菜单) /
    army_confirm(我的军队开战确认) / scouting(对手侦察视图) / home / base / unknown。
    """
    dlg = vision.detect_dialog(frame)
    if dlg.get("present"):
        return "dialog", dlg
    # 夜世界“开始进攻”米色中央面板
    beige = _ratio_in_hsv(_region(frame, (0.30, 0.28, 0.70, 0.75)), (10, 0, 180), (40, 90, 255))
    if beige > 0.45:
        return "attack_menu", {"beige": round(beige, 2)}
    # 主村“我的军队”开战确认面板：右下绿色“进攻！”按钮
    green_br = _ratio_in_hsv(_region(frame, (0.80, 0.84, 1.0, 0.99)), (35, 90, 120), (85, 255, 255))
    if green_br > 0.15:
        return "army_confirm", {"green_br": round(green_br, 2)}
    # 主村联机战斗菜单：左下金色“搜索对手”按钮
    gold_lc = _ratio_in_hsv(_region(frame, (0.04, 0.66, 0.30, 0.84)), (15, 120, 150), (35, 255, 255))
    if gold_lc > 0.25:
        return "battle_menu", {"gold_lc": round(gold_lc, 2)}
    # 右下红色圆按钮（侦察/战斗界面的“进攻”）
    redbr = _ratio_in_hsv(_region(frame, (0.82, 0.80, 1.0, 1.0)), (0, 120, 120), (12, 255, 255))
    if redbr > 0.18:
        return "scouting", {"redbr": round(redbr, 2)}
    # 左下黄色“战斗”
    yellowbl = _ratio_in_hsv(_region(frame, (0.0, 0.78, 0.16, 1.0)), (18, 120, 120), (35, 255, 255))
    if yellowbl > 0.25:
        return "home", {"yellowbl": round(yellowbl, 2)}
    calib, meta = vision.detect_boundary(frame)
    if calib is not None and meta.get("confidence", 0) > 0.25:
        return "base", meta
    return "unknown", {}


# ---------------- 采集器 ----------------

class Farm:
    def __init__(self, serial="127.0.0.1:5555", out="out/farm", mode="sample",
                 live=False, anchors=None, use_llm=False, grid_n=44, logger=print):
        self.a = adbmod.Adb(config.find_adb(), serial)
        self.a.ensure_device()
        self.out = out
        self.mode = mode
        self.live = live
        self.anchors = anchors or load_anchors()
        self.use_llm = use_llm and llm is not None
        self.grid_n = grid_n
        self.log = logger
        self.samples = []
        self.blockers = list(PERSISTENT_BLOCKERS)
        self.stats = {"scouted": 0, "skipped": 0, "attacked": 0, "dialog_recovered": 0,
                      "train_rounds": 0, "errors": 0, "menu_opened": 0}
        os.makedirs(out, exist_ok=True)
        os.makedirs(os.path.join(out, "frames"), exist_ok=True)
        os.makedirs(os.path.join(out, "samples"), exist_ok=True)

    # ---------- 基础动作 ----------
    def tap(self, key, wait=1.0):
        xy = anchor_xy(self.anchors, key)
        self.log(f"[tap] {key} ({xy[0]},{xy[1]}) live={self.live}")
        if self.live:
            self.a.tap(int(xy[0]), int(xy[1]), dry_run=False)
        time.sleep(wait)

    def tap_xy(self, x, y, wait=1.0):
        self.log(f"[tap] xy ({int(x)},{int(y)}) live={self.live}")
        if self.live:
            self.a.tap(int(x), int(y), dry_run=False)
        time.sleep(wait)

    def back(self, wait=1.2):
        """发返回键关闭浮层（不点任何战斗按钮）。"""
        if self.live:
            self.a._run(["shell", "input", "keyevent", "4"])
        time.sleep(wait)

    def shot(self, tag):
        frame, ms, _ = self.a.screencap()
        path = os.path.join(self.out, "frames", f"{tag}.png")
        ok, buf = cv2.imencode(".png", frame)
        buf.tofile(path)
        return frame, path, ms

    def recover(self, tries=6):
        for _ in range(tries):
            frame, _, _ = self.a.screencap()
            dlg = vision.detect_dialog(frame)
            if not dlg.get("present"):
                return True
            btn = dlg.get("reload_btn") or [333, 453]
            self.log(f"[recover] dialog -> 重新载入 @ {btn}")
            if self.live:
                self.a.tap(*btn, dry_run=False)
            self.stats["dialog_recovered"] += 1
            time.sleep(3.0)
        return False

    # ---------- 侦察与样本 ----------
    def capture_sample(self, frame):
        calib, meta = vision.detect_boundary(frame, self.grid_n)
        ts = time.strftime("%Y%m%d_%H%M%S")
        sid = f"s{len(self.samples)+1:03d}_{ts}"
        d = os.path.join(self.out, "samples", sid)
        os.makedirs(d, exist_ok=True)
        fpath = os.path.join(d, "frame.png")
        ok, buf = cv2.imencode(".png", frame)
        buf.tofile(fpath)
        rec = {"id": sid, "time": ts, "frame": fpath,
               "size": [int(frame.shape[1]), int(frame.shape[0])],
               "calib": meta if calib is not None else None, "labels": None,
               "issues": []}
        if calib is not None:
            rec["quad"] = [[float(x), float(y)] for x, y in calib.quad]
        # 建筑数：在标定菱形内做连通域计数
        buildings = 0
        if calib is not None:
            try:
                dets = vision.detect_structures(frame, calib)
                buildings = len(dets)
            except Exception as e:
                rec["issues"].append(f"建筑计数失败: {str(e)[:80]}")
        rec["buildings"] = buildings
        if self.use_llm and llm is not None:
            try:
                buildings_l, used, issues, _ = llm.label_layout(frame, f"{self.grid_n}x{self.grid_n}")
                rec["labels"] = buildings_l
                rec["label_model"] = used
                rec["issues"] = issues
                self.log(f"[llm] {used} 标注 {len(buildings_l)} 个建筑，问题 {len(issues)}")
            except Exception as e:
                rec["issues"].append(f"LLM 标注失败: {str(e)[:80]}")
                self.log(f"[llm] 失败 {str(e)[:80]}")
        with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
        self.samples.append(rec)
        self.stats["scouted"] += 1
        self.log(f"[sample] {sid} 建筑 {buildings}（quad={'有' if calib else '无'}）")
        return rec

    # ---------- 单轮推进 ----------
    def run_once(self):
        """走一轮，返回状态字符串。sample 模式绝不点进攻。"""
        frame, _, _ = self.a.screencap()
        state, detail = probe_state(frame)
        self.log(f"[state] {state} {detail if isinstance(detail, dict) else ''}")

        if state == "dialog":
            self.stats["dialog_recovered"] += 1
            btn = detail.get("reload_btn") or [333, 453]
            if self.live:
                self.a.tap(*btn, dry_run=False)
            time.sleep(3.0)
            return "dialog"

        if state == "home":
            self.tap("battle", 1.6)
            self.stats["menu_opened"] += 1
            return "home->menu"

        if state == "attack_menu":
            # 夜世界开始进攻面板：0 兵被拦截，无法搜索。记录后关闭面板。
            self.log("[blocker] 夜世界 0/9 兵，“立即寻找”被拦截，无法进入搜索；"
                     "编辑军队只打开编成编辑器，不训练。")
            self.blockers.append(PERSISTENT_BLOCKERS[0])
            self.tap("attack_close", 1.4)
            return "attack_menu_blocked"

        if state == "battle_menu":
            # 联机菜单：搜索对手被开战确认门挡住，sample 模式不推进，按返回关菜单自清。
            self.log("[blocker] 主村联机菜单可达；搜索需进入开战确认面板，红线禁止点“进攻！”，停止。")
            self.blockers.append(PERSISTENT_BLOCKERS[1])
            self.back(1.4)
            return "menu_blocked"

        if state == "army_confirm":
            # 红线：绝不在此点“进攻！”。记录并关闭面板退回主页。
            self.log("[blocker] 到达我的军队开战确认面板；红线禁止点“进攻！”，关闭面板退回。")
            self.blockers.append(PERSISTENT_BLOCKERS[1])
            self.tap("confirm_close", 1.6)
            return "confirm_closed"

        if state == "scouting":
            self.capture_sample(frame)
            self.tap("scout_back", 1.4)
            return "scout->back"

        if state in ("base", "unknown"):
            # 非菜单稳定态：不盲点（live 安全），只记录，等待人工/下一轮
            self.log(f"[idle] 状态 {state}，未匹配菜单/主页，不盲目点击")
            return "idle"
        return state

    def run(self, rounds=10, interval=0.8):
        for i in range(rounds):
            try:
                st = self.run_once()
                self.log(f"[round {i+1}/{rounds}] {st}")
            except Exception as e:
                self.stats["errors"] += 1
                self.log(f"[error] {e}")
            time.sleep(interval)
        self.write_report()
        return self.stats

    # ---------- 报告 ----------
    def anchors_table(self):
        rows = []
        for k, v in self.anchors.items():
            rows.append({
                "key": k,
                "point": v.get("point") if isinstance(v, dict) else v,
                "confirmed": bool(v.get("confirmed")) if isinstance(v, dict) else False,
                "note": v.get("note", "") if isinstance(v, dict) else "",
                "evidence": v.get("evidence", []) if isinstance(v, dict) else [],
            })
        return rows

    def write_report(self):
        rep = {
            "mode": self.mode,
            "live": self.live,
            "grid_n": self.grid_n,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stats": self.stats,
            "anchors": self.anchors_table(),
            "samples": [{k: v for k, v in s.items() if k != "labels"} for s in self.samples],
            "blockers": list(dict.fromkeys(self.blockers)),
        }
        path = os.path.join(self.out, "farm_report.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        self.log(f"[report] {path}")
        return path

    def print_anchors(self):
        self.log("== 当前 anchors ==")
        for row in self.anchors_table():
            mark = "CONFIRMED" if row["confirmed"] else "UNCONFIRMED"
            self.log(f"  {row['key']:14s} {row['point']}  [{mark}]  {row['note']}")


def run_cli(args):
    """farm 子命令 CLI 主体，由 cli.py 调用。"""
    from .cli import _ensure_out
    anchors = load_anchors(args.anchors) if getattr(args, "anchors", None) else load_anchors()
    out = _ensure_out(args.out or "out/farm")
    farm = Farm(serial=getattr(args, "serial", "") or "127.0.0.1:5555",
                out=out, mode=args.mode, live=args.live, anchors=anchors,
                grid_n=args.grid, logger=print)
    farm.print_anchors()
    if getattr(args, "print_anchors_only", False):
        return 0
    farm.run(rounds=args.rounds)
    return 0
