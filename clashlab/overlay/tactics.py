# -*- coding: utf-8 -*-
"""双引擎模式：本地规则引擎（离线、确定）/ 大模型战术策略（联网、需等）。

engine=local
  数据源 out/prebattle/info.json 的 exposed —— analysis.py 用覆盖 dps 算出的
  "高价值且外露"防御，含 tile / dps / edge_dist。纯本地、可复现、可解释。
  面板按钮逐个切换聚焦建筑，HUD 按 dps 分档配色高亮。

engine=llm
  同一份 exposed + 盲区 + 核心覆盖 dps 作为上下文，交给 llm.chat 生成三段式策略。
  全程后台线程，GUI 线程只读快照，绝不阻塞渲染。

为什么不做"截图 -> 模板识别建筑类型"：
  实测（tile_px 22/25/28 三档）eagle 最高分 0.584 / p99 0.473，inferno 0.348，
  与背景区分度不足；颜色+形状分割在同一张图上只出 3 个连通块。逐像素模板
  不是主路径，本模块因此不承诺类型识别，只承诺"位置 + dp 威胁排序"。
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time

LOG = logging.getLogger("clashlab.overlay.tactics")

# 名称与档位：dps 高 / 中 / 低 -> 红 / 橙 / 蓝
NAME_ZH = {
    "eagle-artillery": "鹰炮",
    "monolith": "巨石碑",
    "firespitter": "散射炮",
    "scattershot": "散射炮",
    "inferno-tower": "地狱塔",
    "town-hall": "大本营",
    "x-bow": "X 连弩",
    "air-defense": "防空塔",
    "wizard-tower": "法师塔",
    "multi-archer-tower": "多重箭塔",
    "archer-tower": "箭塔",
    "cannon": "加农炮",
    "mortar": "迫击炮",
    "air-sweeper": "空气炮",
    "spell-tower": "法术塔",
    "clan-castle": "部落城堡",
    "storage": "储罐",
    "collector": "采集器",
}

COLOR_HOT = (0.937, 0.337, 0.306, 1.0)     # 最高威胁
COLOR_MID = (0.949, 0.722, 0.282, 1.0)     # 主要火力
COLOR_LOW = (0.471, 0.745, 0.902, 1.0)     # 次要

# 单选状态：pages 与 runtime 共用同一份，保证面板点击立刻反映到 HUD；
# show_threats/show_route 为 v5 LLM 标注 chip 开关（默认开），引擎互斥由 runtime 分支保证
SEL = {"idx": 0, "engine": "local", "show_threats": True, "show_route": True,
       "army": "", "equipment": ""}
OUT_DIR = os.path.join("out", "overlay", "tactics")
PLAN_JSON = "plan.json"

GOALS = ["三星", "两星", "打资源", "清边"]

# 兵种 / 装备下拉选项：id 必须与 knowledge 卡面 army/equipment 字段一致（score_card
# 按 id 集合重叠打分，army+2/equipment+3）；列表只收 44 张卡里实际出现过的 id，
# 卡面没有的不硬塞。assets.py 仅含建筑素材，无兵种/装备清单，故以 KB 卡实有为准。
ARMY_OPTIONS = [
    ("edrag", "雷龙"),
    ("balloon", "气球"),
    ("dragon", "火龙"),
    ("healer", "治疗天使"),
    ("lava-hound", "熔岩猎犬"),
    ("root-rider", "根骑士"),
    ("witch", "女巫"),
    ("ice-golem", "冰戈仑"),
    ("dragon-rider", "龙骑士"),
    ("hog-rider", "野猪骑士"),
    ("super-witch", "超级女巫"),
    ("bat", "蝙蝠"),
    ("super-wizard", "超级法师"),
    ("golem", "戈仑石人"),
    ("miner", "矿工"),
    ("yeti", "雪怪"),
    ("super-archer", "超级弓箭手"),
    ("giant", "巨人"),
    ("bowler", "投石车"),
]

EQUIPMENT_OPTIONS = [
    ("giant-arrow", "巨型箭"),
    ("eternal-tome", "永恒书卷"),
    ("invisibility-vial", "隐形药水"),
    ("action-figure", "动作人偶"),
    ("rocket-spear", "火箭飞矛"),
    ("electro-boots", "雷霆战靴"),
    ("rage-gem", "狂暴宝石"),
    ("haste-vial", "急速药水"),
    ("healing-tome", "治疗书卷"),
    ("giant-gauntlet", "巨化手套"),
    ("spiky-ball", "尖刺足球"),
    ("fireball", "大火球"),
    ("hog-puppet", "野猪木偶"),
    ("frozen-arrow", "冰箭"),
]

# ③ 总预算封顶：联网生成全程不得超过该秒数；超时/全失败立即降级本地规则，
# 不许让玩家在空面板前等多次长调用。30s 覆盖 openai_2 成功样本 7.1–15.5s + 轮换余量
# （探测实测；15s 会把好响应掐死，故不提回 15）。
FALLBACK_BUDGET = 30.0
# 探测实测：openai_2 必须 max_tokens=3000 + reasoning_effort=low 才不空返回；
# 560 预算会被 reasoning_tokens 烧光，finish_reason=length、content_len=0。
PLAN_MAX_TOKENS = 3000
PLAN_REASONING_EFFORT = "low"

# 战术卡库绝对路径（retrieve 默认 dir 相对 CWD 解析，覆盖层 CWD 不定，必须锚定）
_KB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                       "knowledge", "tactics"))

# th 缺失只 WARN 一次（每进程），不刷屏
_TH_WARNED = {"missing": False}


def _dps_of(name, th=None):
    """TH 数值层防御式取 dps：另一路 assets.stats(name, th) 落地前/后都不炸。

    优先 assets.stats(name, th=th)；未落地则回退 assets.STATS 旧表；任何异常返回 0。
    """
    try:
        from .. import assets
        f = getattr(assets, "stats", None)
        if callable(f):
            return int(f(name, th=th).get("dps", 0) or 0)
        return int(assets.STATS.get(name, {}).get("dps", 0) or 0)
    except Exception:
        return 0


_LOCK = threading.Lock()
_JOBS = {"plan": {"state": "idle", "t0": 0.0, "elapsed": 0.0, "err": "", "model": "",
                  "text": "", "goal": "", "fallback": False}}


def _abs(root, rel):
    return rel if os.path.isabs(rel) else os.path.join(root, rel)


# ---------------------------------------------------------------- 本地数据

# 结果级缓存：(root, th) -> (源文件 mtime, doc)；mtime 未变跳过重复 open+json 解析+排序。
_LOCAL_CACHE: dict = {}


def load_local(root, th=None):
    """读本地分析结果，返回排序后的重要防御列表 + 阵型摘要。

    优先 out/prebattle/info.json（analysis 产物）；缺失时退化到 marks.json 的 marks。
    任何异常都返回 ok=False 的空结构，绝不抛给 UI。

    th：可选显式本数（只允许关键字/可选传，位置参数 root 保持兼容）；
    不传则取 info.json 的 "th"。th 为 16 时用 _dps_of(type, th=16) 取 TH16 数值层
    dps 参与降序（覆盖 info.json 旧兜底 dps，取不到再回退 info.json 的 dps）；
    其它本数沿用 info.json 的 dps。th 缺失不猜本数，只 WARN 一次。
    """
    pj = _abs(root, os.path.join("out", "prebattle", "info.json"))
    mk = _abs(root, os.path.join("out", "marks", "marks.json"))
    try:
        mt = os.path.getmtime(pj)
    except OSError:
        try:
            mt = os.path.getmtime(mk)
        except OSError:
            mt = None
    cache_key = (os.path.abspath(root), th)
    hit = _LOCAL_CACHE.get(cache_key)
    if hit is not None and hit[0] == mt:
        return hit[1]

    doc = {"ok": False, "source": "", "rows": [], "blind": [], "counts": {},
           "core_cover_dps": None, "centroid": None, "layout_id": ""}
    th_val = th  # 显式入参优先；None 时再从 info.json 读
    try:
        with open(pj, "r", encoding="utf-8") as f:
            info = json.load(f)
        if th is None:
            th_val = info.get("th")
        exposed = info.get("exposed") or []
        is_th16 = str(th_val).strip() == "16"
        rows = []
        for e in exposed:
            t = str(e.get("type") or "")
            tile = e.get("tile")
            if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
                continue
            # TH16 数值层覆盖旧兜底 dps；取不到（stats 未落地/类型未知）回退 info.json
            override = _dps_of(t, th=16) if is_th16 else 0
            rows.append({
                "type": t,
                "name": NAME_ZH.get(t, t or "未知"),
                "tile": [float(tile[0]), float(tile[1])],
                "dps": override or int(e.get("dps") or 0),
                "edge_dist": e.get("edge_dist"),
            })
        rows.sort(key=lambda r: -r["dps"])
        for i, r in enumerate(rows):
            # 前 3 红、4-6 橙、其余蓝
            r["rank"] = 3 if i < 3 else (2 if i < 6 else 1)
        doc.update({"ok": bool(rows), "source": "prebattle/info.json", "rows": rows,
                    "blind": (info.get("blind") or [])[:6],
                    "counts": info.get("defense_counts") or {},
                    "core_cover_dps": info.get("core_cover_dps"),
                    "centroid": info.get("centroid"),
                    "layout_id": info.get("layout_id") or ""})
    except Exception:
        pass
    if doc["rows"]:
        if th_val not in (None, "", 0):
            doc["th"] = th_val
        elif not _TH_WARNED["missing"]:
            _TH_WARNED["missing"] = True
            LOG.warning("th_missing: info.json 无 th，检索不带本数，dps 沿用旧兜底")
        _clamp_sel(len(doc["rows"]))
        _LOCAL_CACHE[cache_key] = (mt, doc)
        return doc

    # 退化：marks.json 里人工标的 target/avoid
    try:
        with open(_abs(root, os.path.join("out", "marks", "marks.json")), "r",
                  encoding="utf-8") as f:
            marks = json.load(f)
        rows = []
        for m in marks.get("marks") or []:
            tile = m.get("tile")
            if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
                continue
            rows.append({
                "type": m.get("label") or "",
                "name": str(m.get("label") or "未知"),
                "tile": [float(tile[0]), float(tile[1])],
                "dps": 0,
                "edge_dist": None,
                "rank": 3 if m.get("role") == "target" else 2,
            })
        doc.update({"ok": bool(rows), "source": "marks/marks.json", "rows": rows})
        if th not in (None, "", 0):
            doc["th"] = th
    except Exception:
        pass
    _clamp_sel(len(doc["rows"]))
    _LOCAL_CACHE[cache_key] = (mt, doc)
    return doc


def _clamp_sel(n):
    if n <= 0:
        SEL["idx"] = 0
    elif SEL["idx"] >= n:
        SEL["idx"] = n - 1


def selected(doc):
    """当前聚焦行；空列表返回 None。"""
    rows = doc.get("rows") or []
    if not rows:
        return None
    idx = max(0, min(int(SEL.get("idx", 0)), len(rows) - 1))
    return rows[idx]


def color_of(rank):
    return {3: COLOR_HOT, 2: COLOR_MID}.get(rank, COLOR_LOW)


# ---------------------------------------------------------------- 大模型策略

# schema v2：策略 = 结构化 phases 数据（格坐标），由程序渲染成路线图，不再写散文三段。
# 硬性原因（历史证据）：LLM 直接写散文里的坐标不可靠（openai_1 8/8 空返回、
# 方括号坐标被解析器拒）；让模型只产结构化 JSON、坐标由校验器清洗、画图由程序做，
# 省一次重试调用，可控可测。模型失败/JSON 非法/清洗后为空 -> 规则兜底补同样结构，
# 绝不二次调模型（见 _fallback_plan_v2）。
SCHEMA_V2 = 2

SYSTEM_PROMPT = (
    "你是《部落冲突》TH16 进攻战术分析助手。输入是本地规则引擎算出的阵型情报："
    "外露高价值防御（含格坐标与 dps）、核心区覆盖 dps、外圈盲区。\n"
    "【只输出一个 JSON 对象，禁止散文、禁止三段式文字、禁止 markdown 代码块之外的解释】\n"
    "严格按以下结构输出（键名不可改，缺的键给空数组/空字符串）：\n"
    "{\n"
    '  "phases": [\n'
    "    {\n"
    '      "i": 1,                      // 阶段序号，从 1 开始递增\n'
    '      "name": "战前箭清",           // ≤8 个汉字的阶段名\n'
    '      "t_start": 0, "t_end": 8,    // 阶段起止秒数（整数秒，t_start ≤ t_end）\n'
    '      "units": [{"type": "giant-arrow", "count": 1, "drop_tile": [1, 27]}],\n'
    '      "route": [[1, 27], [15, 21], [21, 19]],   // 行进折线格坐标（含投放点）\n'
    '      "targets": [[15, 21], [18, 21], [21, 19]], // 本阶段打击目标格坐标\n'
    '      "purpose": "一箭串掉三座防空，为主军开路"   // 一句话目的，≤40 字\n'
    "    }\n"
    "  ],\n"
    '  "threats": [{"tile": [16, 16], "type": "eagle-artillery", '
    '"why": "射程全图、dps 350，必须先处理"}],\n'
    '  "win_condition": "箭清防空后从真空侧进入，按 dps 顺序拆高价值防御，最后收大本"\n'
    "}\n"
    "硬约束：\n"
    "1. 所有格坐标必须是整数，且 0 ≤ x ≤ 43、0 ≤ y ≤ 43（y 向下）；"
    "禁止小数、禁止越界、禁止编造输入里没有的建筑坐标；\n"
    "2. phases 给 3~4 个阶段：战前预处理（箭/法术）→ 清边进入 → 主力推进 → 收尾；\n"
    "3. route 必须从投放点连到目标点，顺序就是行进顺序；targets 只放本阶段要打的点；\n"
    "4. units.type 只允许输入情报或参考卡里出现过的兵种/装备 id；count 为正整数；\n"
    "5. 数据不足时在 purpose/why 里说明缺什么，不要猜坐标；\n"
    "6. 参考战术卡来自公开攻略，与当前阵型未必匹配：只在真正相关时引用配比，"
    "不相关就不提，禁止为凑数硬套卡面内容。\n"
    "合法示例（仅示范结构，坐标不得照抄，必须用输入给的坐标）：\n"
    '{"phases":[{"i":1,"name":"战前箭清","t_start":0,"t_end":8,'
    '"units":[{"type":"giant-arrow","count":1,"drop_tile":[1,27]}],'
    '"route":[[1,27],[15,21],[21,19]],'
    '"targets":[[15,21],[18,21],[21,19]],'
    '"purpose":"一箭串三座防空"},'
    '{"i":2,"name":"西侧进入","t_start":8,"t_end":40,'
    '"units":[{"type":"edrag","count":3,"drop_tile":[1,28]}],'
    '"route":[[1,28],[8,33],[12,30]],'
    '"targets":[[8,33],[12,30]],'
    '"purpose":"从真空侧贴边清进"},'
    '{"i":3,"name":"主力推进","t_start":40,"t_end":120,'
    '"units":[{"type":"edrag","count":4,"drop_tile":[1,28]}],'
    '"route":[[12,30],[17,28],[16,38]],'
    '"targets":[[17,28],[16,38]],'
    '"purpose":"按 dps 顺序拆高价值防御"},'
    '{"i":4,"name":"收尾","t_start":120,"t_end":190,'
    '"units":[],"route":[[17,28],[23,43]],'
    '"targets":[[23,43]],"purpose":"清残兵收边"}],"threats":'
    '[{"tile":[16,16],"type":"eagle-artillery","why":"射程全图必须先拆"}],'
    '"win_condition":"箭清防空后真空侧进入，拆高价值防御收大本"}'
)


# ---------------------------------------------------------------- 战术知识库注入

def _kb_brief(doc, goal="三星", army=None, equipment=None, pattern=None):
    """诚实构造 knowledge.retrieve 的 brief：doc 里有什么就带什么，没有的键不出现，绝不猜。

    - th：仅 doc 带 th 键时填（load_local 只在 info.json/显式入参有值时才写 th）；
    - army / equipment：当前无数据源，只能由调用方经可选参数透传，默认空；
    - pattern：可选透传，默认空；
    - keywords：只取 doc 里真实存在的词（rows 的 type 名 / 中文名、goal）。
    """
    brief = {}
    th = doc.get("th")
    if th not in (None, "", 0):
        brief["th"] = th
    if army:
        brief["army"] = [army] if isinstance(army, str) else list(army)
    if equipment:
        brief["equipment"] = ([equipment] if isinstance(equipment, str)
                              else list(equipment))
    if pattern:
        brief["pattern"] = pattern
    kws = []
    for r in doc.get("rows") or []:
        for v in (r.get("type"), r.get("name")):
            v = str(v or "").strip()
            if v and v not in kws:
                kws.append(v)
    if goal:
        kws.append(str(goal))
    if kws:
        brief["keywords"] = kws
    return brief


def _collect_kb(brief):
    """调 knowledge.retrieve；模块缺失/异常一律返回 []，绝不炸策略生成。"""
    try:
        from .. import knowledge
        if not callable(getattr(knowledge, "retrieve", None)):
            return []
        return knowledge.retrieve(brief=brief, k=3, dir=_KB_DIR) or []
    except Exception as e:
        LOG.warning("knowledge 检索失败（不阻塞）: %r", e)
        return []


def _card_digest(card):
    """卡面压缩成一行：优先 summary/body，否则首条 key_points，再退标题；截断防撑爆。"""
    text = (card.get("summary") or card.get("body")
            or (card.get("key_points") or [""])[0]
            or (card.get("source") or {}).get("title") or "")
    return " ".join(str(text).split())[:80]


def _card_line(card, reasons):
    """注入 user message 的单行卡：id | th | pattern | conf | 摘要（命中理由）。"""
    th = card.get("th") or "-"
    pat = card.get("pattern") or "-"
    conf = card.get("confidence")
    conf_s = f"{float(conf):.2f}" if isinstance(conf, (int, float)) else "-"
    reason = "；".join(r for r in reasons if not str(r).startswith("score="))
    tail = f"（命中：{reason}）" if reason else ""
    return (f"{card.get('id', '?')} | th{th} | {pat} | conf {conf_s} | "
            f"{_card_digest(card)}{tail}")


def build_messages(doc, goal="三星", sel=None, extra="",
                   army=None, equipment=None, pattern=None):
    rows = doc.get("rows") or []
    lines = []
    for i, r in enumerate(rows, 1):
        ed = f" 距边{r['edge_dist']}格" if r.get("edge_dist") is not None else ""
        lines.append(f"{i}. {r['name']}({r['type']}) 格({r['tile'][0]:.0f},{r['tile'][1]:.0f}) "
                     f"dps {r['dps']}{ed}")
    if not lines:
        lines.append("（无外露防御数据）")
    ctx = []
    if doc.get("core_cover_dps"):
        ctx.append(f"核心区覆盖 dps {doc['core_cover_dps']}")
    if doc.get("centroid"):
        ctx.append(f"防御重心格({doc['centroid'][0]:.1f},{doc['centroid'][1]:.1f})")
    blind = doc.get("blind") or []
    if blind:
        b = blind[0]
        ctx.append(f"最近盲区格({b.get('tile', [0, 0])[0]},{b.get('tile', [0, 0])[1]})"
                   f" 覆盖 {b.get('cover', 0)} dps")
    focus = ""
    if sel:
        focus = (f"\n当前用户聚焦：{sel['name']} 格({sel['tile'][0]:.0f},{sel['tile'][1]:.0f})，"
                 f"请围绕它安排拆除顺序。")
    user = ("外露高价值防御（已按 dps 降序）：\n" + "\n".join(lines) +
            ("\n阵型摘要：" + "；".join(ctx) if ctx else "") +
            f"\n进攻目标：{goal}{focus}" +
            (f"\n补充：{extra}" if extra else ""))
    # 战术知识库注入：无命中不加该段，user message 不出现"参考卡"字样，不编造卡片
    brief = _kb_brief(doc, goal=goal, army=army, equipment=equipment, pattern=pattern)
    hits = _collect_kb(brief)
    if hits:
        kb = ["", "参考战术卡（公开攻略摘录，与当前阵型未必匹配，只在真正相关时引用）："]
        kb += [_card_line(c, r) for c, r in hits]
        user += "\n".join(kb)
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user}]


def _local_fallback_text(doc, goal="三星"):
    """③ 本地规则兜底三段式：直接用 doc.rows（dps 降序）拼可读中文，带格(x,y)
    让 parse_plan_marks 仍能抽出威胁/路线点；不编造输入里没有的建筑。"""
    rows = doc.get("rows") or []
    top = rows[:3]
    threat = "；".join(
        f"{r['name']} 格({r['tile'][0]:.0f},{r['tile'][1]:.0f})（dps {r['dps']}）"
        for r in top) or "（本地情报无外露防御，建议先侦察）"
    route = " → ".join(
        f"{r['name']} 格({r['tile'][0]:.0f},{r['tile'][1]:.0f})" for r in rows[:4]
    ) or "（待侦察后定路线）"
    return (
        f"【威胁排序】{threat}。\n"
        f"【进攻路线】按 dps 降序清边后拆除：{route}；核心覆盖重区先绕边清掉再进。\n"
        f"【兵种与法术】本地规则建议：先清边铺主力，高 dps 点用法术配合拆除；"
        f"具体配比待联网模型复核。\n"
        f"（目标：{goal}；本段为本地规则分析，非大模型生成）"
    )


# ---------------------------------------------------------------- schema v2 校验
#
# 模型输出一律当不可信输入：坐标非整数/越界/类型错 -> 清洗丢弃该条；清洗后
# phases 为空才算硬失败（调兜底）。越界单点不否决整份方案（软清洗）。

def _clean_tile(v):
    """格坐标清洗：必须是两个可转 int 的数，0..43；非法返回 None。"""
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        return None
    try:
        x, y = int(round(float(v[0]))), int(round(float(v[1])))
    except (TypeError, ValueError, OverflowError):
        return None
    if not (0 <= x <= _GRID_MAX and 0 <= y <= _GRID_MAX):
        return None
    return [x, y]


def _clean_tile_list(seq):
    out = []
    for v in seq or []:
        t = _clean_tile(v)
        if t is not None and t not in out:
            out.append(t)
    return out


def _clean_phase(obj, idx, issues):
    """单阶段清洗；非法字段丢弃、不抛栈。返回 None 表示整条阶段不可用。"""
    if not isinstance(obj, dict):
        issues.append(f"[soft] phase#{idx} 不是对象，已跳过")
        return None
    name = str(obj.get("name") or f"阶段{idx}")[:12]
    try:
        t_start = float(obj.get("t_start", 0) or 0)
        t_end = float(obj.get("t_end", 0) or 0)
    except (TypeError, ValueError):
        t_start, t_end = 0.0, 0.0
    if t_end < t_start:
        t_start, t_end = t_end, t_start
    units = []
    for u in (obj.get("units") or [])[:6]:
        if not isinstance(u, dict):
            continue
        utype = str(u.get("type") or "").strip()[:24]
        try:
            count = max(1, int(u.get("count", 1) or 1))
        except (TypeError, ValueError):
            count = 1
        drop = _clean_tile(u.get("drop_tile"))
        if not utype:
            continue
        units.append({"type": utype, "count": count, "drop_tile": drop})
    route = _clean_tile_list(obj.get("route"))
    targets = _clean_tile_list(obj.get("targets"))
    if not route and not targets:
        issues.append(f"[soft] phase#{idx}({name}) 无合法 route/targets 坐标，已跳过")
        return None
    return {
        "i": int(obj.get("i") or idx),
        "name": name,
        "t_start": round(t_start, 1),
        "t_end": round(t_end, 1),
        "units": units,
        "route": route,
        "targets": targets,
        "purpose": str(obj.get("purpose") or "")[:80],
    }


def _validate_plan_v2(obj):
    """清洗模型 JSON -> (clean, issues, hard)。

    hard=True：不是对象 / 清洗后 phases 为空，整条拒收走规则兜底。
    越界坐标、非法单元等只软清洗，不否决整份。
    clean = {"phases":[...], "threats":[...], "win_condition": str}
    """
    issues = []
    clean = {"phases": [], "threats": [], "win_condition": ""}
    if not isinstance(obj, dict):
        return clean, ["[hard] 输出不是 JSON 对象"], True
    raw_phases = obj.get("phases")
    if not isinstance(raw_phases, list):
        return clean, ["[hard] 缺少 phases 数组"], True
    for idx, p in enumerate(raw_phases[:6], 1):
        ph = _clean_phase(p, idx, issues)
        if ph is not None:
            clean["phases"].append(ph)
    for th in (obj.get("threats") or [])[:8]:
        if not isinstance(th, dict):
            continue
        tile = _clean_tile(th.get("tile"))
        if tile is None:
            continue
        clean["threats"].append({
            "tile": tile,
            "type": str(th.get("type") or "")[:24],
            "why": str(th.get("why") or "")[:80],
        })
    clean["win_condition"] = str(obj.get("win_condition") or "")[:200]
    if not clean["phases"]:
        issues.append("[hard] 清洗后 phases 为空")
        return clean, issues, True
    # 阶段序号重排，防模型跳号/重号
    for i, ph in enumerate(clean["phases"], 1):
        ph["i"] = i
    return clean, issues, False


# ---------------------------------------------------------------- schema v2 规则兜底
#
# 模型不可用 / JSON 非法 / 清洗后为空时，用 doc.rows（dps 降序）+ 几何规则补出
# 结构完整的 phases：战前箭清 -> 清边进入 -> 主力推进 -> 收尾。不二次调模型。
# 时间区间为规则占位（假设值，渲染器照画，HUD 内嵌后由实战节奏覆盖）。

_FALLBACK_SCHEDULE = [(0, 8), (8, 40), (40, 120), (120, 190)]


def _edge_entry(rows, centroid):
    """从四边中点候选里挑离防御重心最远的撒兵点（最薄侧进入）。

    无 centroid 时用 rows 均值；rows 也空时回退西缘 (1,22)。
    """
    cx, cy = 21.5, 21.5
    if isinstance(centroid, (list, tuple)) and len(centroid) == 2:
        try:
            cx, cy = float(centroid[0]), float(centroid[1])
        except (TypeError, ValueError):
            pass
    elif rows:
        cx = sum(r["tile"][0] for r in rows) / len(rows)
        cy = sum(r["tile"][1] for r in rows) / len(rows)
    cands = [(1, 22), (42, 22), (22, 1), (22, 42)]  # 西/东/北/南 边中点
    best = max(cands, key=lambda c: (c[0] - cx) ** 2 + (c[1] - cy) ** 2)
    return list(best)


def _fallback_plan_v2(doc, goal="三星", sel=None, extra=""):
    """规则兜底：产出结构完整的 v2 phases/threats/win_condition。

    与 _local_fallback_text 同源（都吃 doc.rows），但本函数产结构化数据供渲染器画图，
    不依赖模型、不编造输入里没有的建筑。返回 (clean, text)；text 供旧面板/旧解析用。
    """
    rows = doc.get("rows") or []
    text = _local_fallback_text(doc, goal=goal)
    centroid = doc.get("centroid")
    top = rows[:5]
    phases, threats = [], []

    def _it(r):
        return [int(round(r["tile"][0])), int(round(r["tile"][1]))]

    # 阶段1 战前箭清：优先防空（对空命门），其次 dps 最高 1~3 座
    ad = [r for r in rows if r.get("type") == "air-defense"][:3]
    pre = ad or top[:3]
    entry = _edge_entry(rows, centroid)
    if pre:
        standoff = [max(1, int(pre[0]["tile"][0]) - 4),
                    max(1, int(pre[0]["tile"][1]) - 2)]
        phases.append({
            "i": 1, "name": "战前箭清",
            "t_start": _FALLBACK_SCHEDULE[0][0], "t_end": _FALLBACK_SCHEDULE[0][1],
            "units": [{"type": "giant-arrow", "count": 1, "drop_tile": standoff}],
            "route": [standoff] + [_it(r) for r in pre],
            "targets": [_it(r) for r in pre],
            "purpose": "开局先清对空/高 dps 点，为主军开路（规则按 dps 排序，非模型判断）",
        })
    # 阶段2 清边进入：从最薄侧边缘点贴边清到第一座目标
    if top:
        phases.append({
            "i": 2, "name": "清边进入",
            "t_start": _FALLBACK_SCHEDULE[1][0], "t_end": _FALLBACK_SCHEDULE[1][1],
            "units": [{"type": "edrag", "count": 3, "drop_tile": entry}],
            "route": [entry, _it(top[0])],
            "targets": [_it(top[0])],
            "purpose": "从防御最薄侧贴边清进，避开重火力簇",
        })
    # 阶段3 主力推进：按 dps 降序逐座拆
    rest = top[1:4] or top
    if rest:
        mid = [entry] + [_it(r) for r in rest]
        phases.append({
            "i": 3, "name": "主力推进",
            "t_start": _FALLBACK_SCHEDULE[2][0], "t_end": _FALLBACK_SCHEDULE[2][1],
            "units": [{"type": "edrag", "count": 4, "drop_tile": entry}],
            "route": mid,
            "targets": [_it(r) for r in rest],
            "purpose": "按 dps 降序拆除高价值外露防御",
        })
    # 阶段4 收尾：大本营若在情报里则收，否则收最后一座目标
    th = next((r for r in rows if r.get("type") == "town-hall"), None)
    last = th or (rest[-1] if rest else None)
    if last:
        lt = _it(last)
        phases.append({
            "i": 4, "name": "收尾",
            "t_start": _FALLBACK_SCHEDULE[3][0], "t_end": _FALLBACK_SCHEDULE[3][1],
            "units": [],
            "route": [lt],
            "targets": [lt],
            "purpose": "收残兵、推平剩余建筑",
        })
    for i, r in enumerate(top, 1):
        threats.append({
            "tile": [int(r["tile"][0]), int(r["tile"][1])],
            "type": r.get("type") or "",
            "why": f"{r['name']} dps {r['dps']}，外露，需优先处理（规则排序）",
        })
    win = (f"目标{goal}：战前清掉对空/高 dps 点，从最薄侧进入，"
           f"按 dps 顺序拆高价值防御后收大本（规则兜底，非模型生成）")
    for i, ph in enumerate(phases, 1):
        ph["i"] = i
    return {"phases": phases, "threats": threats, "win_condition": win}, text


def _synthesize_text_v2(clean, goal):
    """把清洗后的 v2 结构合成三段式可读文本：旧面板直接显示、parse_plan_marks 抽旧标注。

    v2 主消费是渲染器（phases/threats）；这段文本只保 v5 兼容，不追求模型级文采。
    """
    sec_threat, sec_route, sec_unit = [], [], []
    for th in clean.get("threats") or []:
        t = th["tile"]
        sec_threat.append(f"{th.get('type') or '目标'} 格({t[0]},{t[1]})"
                          f"（{th.get('why') or '需优先处理'}）")
    for ph in clean.get("phases") or []:
        pts = " → ".join(f"格({x},{y})" for x, y in ph.get("route") or [])
        sec_route.append(f"{ph['name']}（{ph['t_start']:.0f}-{ph['t_end']:.0f}s）：{pts}")
        for u in ph.get("units") or []:
            sec_unit.append(f"{u['type']}×{u['count']} 投于格({u['drop_tile'][0]},{u['drop_tile'][1]})"
                            if u.get("drop_tile") else f"{u['type']}×{u['count']}")
    return (
        f"【威胁排序】{'；'.join(sec_threat) or '（本地情报无外露防御，建议先侦察）'}。\n"
        f"【进攻路线】{'；'.join(sec_route) or '（待侦察后定路线）'}。\n"
        f"【兵种与法术】{'；'.join(sec_unit) or '本地规则建议：先清边铺主力，高 dps 点用法术配合拆除。'}\n"
        f"（目标：{goal}；结构化 phases 见 plan.json，本行为兼容展示）"
    )


def _atomic_write_json(path, payload):
    """原子写：先写同目录 *.tmp（flush+fsync），再 os.replace 原子替换目标。
    tmp 与目标同目录必然同卷，replace 在同卷内为原子改名，读取方（主线程
    每 1.5s load_plan）只会看到旧完整文件或新完整文件，绝不会读到半截 JSON。
    异常时清理 tmp，不留残骸。"""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        raise


def _save_fallback_plan(root, payload):
    """兜底结果同样写 plan.json，保证重启/切引擎后面板不停在空白、HUD 有本地标注。"""
    path = os.path.join(_abs(root, OUT_DIR), PLAN_JSON)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _atomic_write_json(path, payload)


def plan(root, doc, goal="三星", sel=None, extra="",
         army=None, equipment=None, pattern=None, timeout=40, attempts=3,
         deadline=None):
    """同步请求策略；结果写盘。失败抛异常，由调用方降级。

    provider 链 openai_2 -> openai_1（llm.chat 内部轮换）；空 content/异常换下一个。
    deadline：总预算 perf_counter 时间戳；到点立即停止重试，不把 attempts×timeout 跑完。
    不带 deadline 时保持旧行为（兼容 CLI/其他调用方）。

    army/equipment/pattern：可选透传给战术知识库检索，默认空（当前无数据源，不伪造）。
    落盘新增 kb_brief（实际传给 retrieve 的 brief，便于复现）与 kb_cards
    （命中卡 id + 命中理由/分数）。
    """
    from .. import llm
    msgs = build_messages(doc, goal=goal, sel=sel, extra=extra,
                          army=army, equipment=equipment, pattern=pattern)
    t0 = time.perf_counter()
    text = used = None
    last_err = None
    for _ in range(max(1, attempts)):
        if deadline is not None:
            remain = deadline - time.perf_counter()
            if remain <= 1.0:
                break
            call_timeout = min(timeout, remain)
        else:
            call_timeout = timeout
        try:
            text, used = llm.chat(msgs, temperature=0.25,
                                  max_tokens=PLAN_MAX_TOKENS,
                                  reasoning_effort=PLAN_REASONING_EFFORT,
                                  timeout=call_timeout)
            break
        except Exception as e:
            last_err = e
            if deadline is not None and time.perf_counter() >= deadline:
                break
            time.sleep(1.2)
    if text is None:
        raise last_err or RuntimeError("策略生成失败")
    text = llm.redact_secrets((text or "").strip())

    # schema v2：模型只产结构化 JSON；extract_json 失败 / 清洗后 phases 为空
    # -> 抛错由调用方走规则兜底（_fallback_plan_v2），绝不二次调模型。
    obj = llm.extract_json(text)
    clean, v2_issues, hard = _validate_plan_v2(obj)
    if hard:
        raise RuntimeError("结构化策略 JSON 非法：" + ";".join(v2_issues)[:160])
    synth_text = _synthesize_text_v2(clean, goal)

    # 检索复现：与 build_messages 同口径，落盘 brief + 命中证据
    kb_brief = _kb_brief(doc, goal=goal, army=army, equipment=equipment, pattern=pattern)
    kb_hits = _collect_kb(kb_brief)
    kb_cards = []
    for card, reasons in kb_hits:
        score = None
        kept = []
        for r in reasons:
            if str(r).startswith("score="):
                try:
                    score = float(str(r).split("=", 1)[1])
                except (ValueError, IndexError):
                    pass
            else:
                kept.append(r)
        kb_cards.append({
            "id": card.get("id"),
            "th": card.get("th") or "",
            "pattern": card.get("pattern") or "",
            "confidence": card.get("confidence"),
            "score": score,
            "reasons": kept,
            "digest": _card_digest(card),
        })

    # v5 兼容：从合成三段式文本抽 threats/route 旧标注（独立函数，失败返回空）；
    # 旧 plan.json 无 marks 键 -> 绘制层按空处理，退回原 pins 行为，不报错
    marks = parse_plan_marks({"text": synth_text})

    out = {
        "ok": True, "goal": goal, "sel": (sel or {}).get("name", ""),
        "model": used, "elapsed": round(time.perf_counter() - t0, 2),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "schema_version": SCHEMA_V2,
        # v2 主数据：渲染器直接吃 phases/threats/win_condition
        "phases": clean["phases"],
        "threats": clean["threats"],
        "win_condition": clean["win_condition"],
        "v2_issues": v2_issues,
        # v5 兼容字段：旧面板显示 + 旧 HUD 标注
        "text": synth_text,
        "raw": text,
        "marks": marks,
        "kb_brief": kb_brief,
        "kb_cards": kb_cards,
    }
    path = os.path.join(_abs(root, OUT_DIR), PLAN_JSON)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _atomic_write_json(path, out)
    return out


def load_plan(root):
    path = os.path.join(_abs(root, OUT_DIR), PLAN_JSON)
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        if isinstance(doc, dict) and doc.get("text"):
            return doc
    except Exception:
        pass
    return {"ok": False, "text": "", "model": "", "goal": "", "elapsed": 0.0}


# ---------------------------------------------------------------- v5 策略标注解析
#
# 独立新函数：不改 plan() 已有字段、不碰 kb_cards。只把三段式文本里的
# 「建筑名 格(x,y)」抽成 threats/route 两组点；解析失败（空文本/无段/无合法坐标/
# 格号越界 0..43）返回空结构并 LOG plan_marks: parse_fail，绘制层 0 标注（R1）。

# 坐标本体：半/全角括号，整数或一位小数；建筑名由已知表向后回找（H2：标签只能是
# 建筑名 ≤4 字，不许把「先处理/其次/绕至」等动词句段搬上当标签）
_MARK_RE = re.compile(
    r"格?\s*[(（]\s*(\d+(?:\.\d+)?)\s*[,，]\s*(\d+(?:\.\d+)?)\s*[)）]")
# 裸「格(x,y)」绕开区（绕开/避开…重区）无建筑名，上下文命中即跳过，不误抓
_AVOID_CTX = re.compile(r"绕开|避开|重区|覆盖|盲区")
_GRID_MAX = 43

_KNOWN_CACHE: list = []


def _known_aliases():
    """NAME_ZH 中文名 + 英文 type 名（长名优先，防空塔/散射炮先于单字匹配）。"""
    if _KNOWN_CACHE:
        return _KNOWN_CACHE
    vals = set()
    for en, zh in NAME_ZH.items():
        vals.add(zh)
        vals.add(en)
    _KNOWN_CACHE.extend(sorted(vals, key=len, reverse=True))
    return _KNOWN_CACHE


def _label_before(sec, start):
    """在坐标前 12 字窗内回找已知建筑名：取离括号最近的那个（防链上前面的
    建筑名被 rfind 误配）；找不到返回 None（不猜标签）。"""
    window = sec[max(0, start - 12):start]
    best, best_end = None, -1
    for name in _known_aliases():
        idx = window.rfind(name)
        if idx >= 0:
            end = idx + len(name)
            if end > best_end:
                best, best_end = name, end
    return best


def _section(text, head, following):
    """取【head】段正文，止于下一个【】标题或文末；缺段返回空串。"""
    alt = "|".join(following)
    m = re.search(rf"【{head}】\s*(.*?)(?=【(?:{alt})】|$)", text, re.S)
    return m.group(1).strip() if m else ""


def _short_label(name):
    """H2：标签 ≤4 中文字；去空格/格字/标点，截前 4 字，绝不带句段。"""
    s = re.sub(r"[\s格,，。.、:：()（）]", "", str(name or ""))
    return s[:4]


def _pairs(sec):
    """段内抽 (label, tile)；格号越界/非数字/无已知建筑名/绕开区一律跳过，不猜。"""
    out = []
    for m in _MARK_RE.finditer(sec):
        ctx = sec[max(0, m.start() - 4):m.start()]
        if _AVOID_CTX.search(ctx):
            continue  # 绕开/避开重区的裸格坐标不是标注点
        label = _label_before(sec, m.start())
        if label is None:
            continue  # 找不到已知建筑名 -> 不画（R1：不猜标签）
        sx, sy = m.group(1), m.group(2)
        try:
            x, y = float(sx), float(sy)
        except ValueError:
            continue
        if not (0.0 <= x <= _GRID_MAX and 0.0 <= y <= _GRID_MAX):
            continue  # H1：越界格不画，防飘到角落空地
        out.append({"label": _short_label(label),
                    "tile": [int(round(x)), int(round(y))]})
    return out


def parse_plan_marks(plan):
    """plan dict 或文本 -> {"threats":[...], "route":[...]}；失败返回空并记 parse_fail。

    threats: [{"tile":[x,y],"label":"鹰炮","rank":1}]（rank=段内顺序，1 最高威胁）
    route:   [{"seq":1,"tile":[x,y],"label":"进"}]（顺序保留；起点「进」由绘制层补）
    """
    text = plan.get("text") if isinstance(plan, dict) else (plan or "")
    result = {"threats": [], "route": []}
    if not text or not str(text).strip():
        LOG.warning("plan_marks: parse_fail empty text")
        return result
    threat_sec = _section(text, "威胁排序", ["进攻路线", "兵种与法术"])
    route_sec = _section(text, "进攻路线", ["兵种与法术"])
    if not threat_sec and not route_sec:
        LOG.warning("plan_marks: parse_fail missing sections")
        return result
    threats = _pairs(threat_sec)
    for i, t in enumerate(threats[:5], 1):
        t["rank"] = i
    route = _pairs(route_sec)
    for i, r in enumerate(route[:6], 1):
        r["seq"] = i
    result["threats"] = threats[:5]
    result["route"] = route[:6]
    if not result["threats"] and not result["route"]:
        LOG.warning("plan_marks: parse_fail no valid coords")
    return result


def _patch(**kw):
    with _LOCK:
        _JOBS["plan"].update(kw)


def job():
    """GUI 侧快照：运行中附已耗时秒数。"""
    with _LOCK:
        snap = dict(_JOBS["plan"])
    if snap["state"] == "run":
        snap["now"] = round(time.perf_counter() - snap["t0"], 1)
    return snap


def busy():
    return job()["state"] == "run"


def start_plan(root, doc, goal="三星", sel=None, extra="",
               army=None, equipment=None, pattern=None):
    """后台线程请求策略；已在跑就忽略。army/equipment/pattern 透传给知识库检索。"""
    if busy():
        return False
    _patch(state="run", t0=time.perf_counter(), elapsed=0.0, err="", text="",
           model="", goal=goal)

    def _work():
        t0 = time.perf_counter()
        deadline = t0 + FALLBACK_BUDGET
        try:
            out = plan(root, doc, goal=goal, sel=sel, extra=extra,
                       army=army, equipment=equipment, pattern=pattern,
                       deadline=deadline)
            _patch(state="done", elapsed=out.get("elapsed", 0.0),
                   text=out.get("text", ""), model=out.get("model", ""), err="",
                   fallback=False)
        except Exception as e:
            # ③ 全失败/超时 -> 自动降级本地规则分析，面板不允许停在空白；
            # schema v2：兜底同样产出结构完整的 phases/threats/win_condition，
            # 渲染器照图画（关键验收点：兜底必须也能出图），不二次调模型。
            reason = str(e)[:160]
            fb_clean, fb_text = _fallback_plan_v2(doc, goal=goal, sel=sel,
                                                  extra=extra)
            fb_marks = parse_plan_marks({"text": fb_text})
            elapsed = round(time.perf_counter() - t0, 2)
            _save_fallback_plan(root, {
                "ok": False, "fallback": True, "goal": goal,
                "model": "本地规则", "elapsed": elapsed,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "schema_version": SCHEMA_V2,
                "phases": fb_clean["phases"],
                "threats": fb_clean["threats"],
                "win_condition": fb_clean["win_condition"],
                "text": fb_text, "marks": fb_marks,
                "reason": reason,
            })
            _patch(state="fallback", elapsed=elapsed, text=fb_text,
                   model="本地规则", err=reason, fallback=True, goal=goal)

    threading.Thread(target=_work, name="clashlab-plan", daemon=True).start()
    return True


# ---------------------------------------------------------------- CLI

if __name__ == "__main__":
    import sys
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    doc = load_local(root)
    print(f"source={doc['source']} rows={len(doc['rows'])} core_dps={doc['core_cover_dps']}")
    for i, r in enumerate(doc["rows"], 1):
        print(f"  {i}. rank{r['rank']} {r['name']:<6} 格({r['tile'][0]:.0f},{r['tile'][1]:.0f}) "
              f"dps {r['dps']:>4} 距边 {r['edge_dist']}")
    if "--plan" in sys.argv:
        out = plan(root, doc, goal="三星", sel=selected(doc))
        print(f"\n[{out['model']} {out['elapsed']}s]")
        print(out["text"])
