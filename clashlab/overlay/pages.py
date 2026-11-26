# -*- coding: utf-8 -*-
"""PANEL 三页 ImGui 绘制：研究 research / 采集 collect / 设置 setting。

契约入口：draw_panel(ctx, state)，签名固定。
坐标口径：面板全局像素 -> 渲染坐标（1280x720）只走 editor.ViewTransform；
tile<->px 只走 ctx.geo（Calib）。本文件不建窗、不弹窗、不写 config。

视觉规则（见 out/overlay/ui_style.md）：
  * 面板先画实底半透明底板（alpha 0.86，圆角 8，四周 padding 14），内容裁进底板；
  * 标签 font_ready=True 只显示中文；False 才降级 ASCII，绝不中英并排；
  * 按钮高 28px，行间距 8px，中文按钮自适应宽度；
  * 操作提示单独一行；计数/页码收进底部独立状态栏。
"""
from __future__ import annotations

import ctypes
import json
import os
import time

try:  # 可见模式才需要 imgui_bundle；导入失败降级为空绘制，不影响不可见自检
    from imgui_bundle import imgui
except Exception:  # pragma: no cover
    imgui = None

from . import data
from . import keys as keybind
from . import tactics
from . import theme
from . import lang
from .editor import EditorModel, ViewTransform, Rect

PAGE_RESEARCH = "Research"
PAGE_LAYOUT = "Layout"
PAGE_COLLECT = "Capture"
PAGE_SETTING = "Settings"
# 引擎模式：local=本地规则引擎（离线、确定）/ llm=大模型战术策略（联网、异步）
ENGINE_LOCAL = "local"
ENGINE_LLM = "llm"

# 会话态：跨帧保留编辑器模型/拖拽/冻结提示；热重载见 _ensure_model
_SESSION = {
    "model": None,
    "sig": None,
    "freeze_ok": None,
    "freeze_msg": "",
    "freeze_path": "",
    "threshold": 0.0,
    "add_mode": False,
    "new_rect": None,
    "prev_left": False,
    "prev_right": False,
    "anchor_sel": None,
    "offset_dx": None,
    "offset_dy": None,
    "canvas_rect": None,
    # 引擎模式下的本地情报缓存（避免每帧读盘）
    "doc": None,
    "doc_t": 0.0,
    "doc_root": "",
    "plan": None,
    "plan_t": 0.0,
    "goal": "三星",
    # 绑键设置页：捕获态 / 提示消息 / 边沿检测 / 已载入根
    "keys_capture": None,
    "keys_msg": None,
    "keys_prev_vk": {},
    "keys_loaded_root": None,
}

# 视觉 token 一律取 theme（方案 A）；此处只做别名，禁止本地再写色值
GREEN = theme.SUCCESS
YELLOW = theme.WARN
RED = theme.DANGER
INK = theme.INK
SUBTLE = theme.SUB
GREY = theme.SUB
DIM = (0.60, 0.64, 0.68, 1.0)  # 仅未验证/禁用项，仍可辨
PANEL_BG = theme.PANEL_BG
PANEL_BORDER = theme.PANEL_BORDER
PAD = 14.0
BTN_H = 28.0
GAP = 8.0


def _col(rgba):
    return imgui.color_convert_float4_to_u32(imgui.ImVec4(*rgba))


# 正文兵种 id 补名（NAME_ZH / plan_render._ZH_FALLBACK 未覆盖的军种）
_BODY_ID_ZH = {
    "giant-arrow": "巨箭", "balloon": "气球", "edrag": "雷龙",
    "dragon": "火龙", "healer": "治疗天使", "lava-hound": "熔岩猎犬",
}


def _zh_body(text):
    """策略正文里的原始英文 type/兵种 id 统一替换成中文，与下方 Threats 块
    命名一致；先长后短替换防子串截断（eagle-artillery 先于 artillery）。
    替换后正文为中文为主，text_wrapped 不会再从英文单词中间劈开。"""
    if not text:
        return text
    table = {}
    try:
        from .plan_render import _ZH_FALLBACK
        table.update(_ZH_FALLBACK)
    except Exception:
        pass
    table.update(tactics.NAME_ZH)
    table.update(_BODY_ID_ZH)
    for en in sorted(table, key=len, reverse=True):
        if en:
            text = text.replace(en, table[en])
    return text


def _strip_dupe(body):
    """去重：【进攻路线】【威胁排序】明细段与下方 Phases/Threats 块重复，
    正文不再画第二遍；只保留【兵种与战法】等不重复段落。"""
    if not body:
        return body
    out = []
    for seg in body.split("【"):
        if "】" in seg:
            head = seg[:seg.index("】")]
            if head in ("进攻路线", "威胁排序"):
                continue
        out.append(seg)
    return "【".join(out).strip()


def _btn(label, size, *, kind="sec", active=False, disabled=False, key=None, tip=None):
    """统一按钮（C1/C2）：主=绿系三态，次=灰系三态；disabled alpha 0.45 不可点。

    三态：常态填充；hover 提亮 8%（theme.primary/secondary_states hover）；
    按下压暗 12% 并画 1px 内描边。调用前已 set_cursor_screen_pos。
    kind: "pri" 主操作绿 / "sec" 次要灰；active 仅用于外观高亮提示，不改变三态。
    """
    io = imgui.get_io()
    fid = key or label
    if disabled:
        imgui.push_style_color(imgui.Col_.button, theme.DISABLED_BG)
        imgui.push_style_color(imgui.Col_.button_hovered, theme.DISABLED_BG)
        imgui.push_style_color(imgui.Col_.button_active, theme.DISABLED_BG)
        imgui.push_style_color(imgui.Col_.text, theme.DIS_TXT)
        imgui.button(f"{label}##{fid}", size)
        if tip and imgui.is_item_hovered():
            imgui.set_tooltip(tip + "（当前不可用）")
        for _ in range(4):
            imgui.pop_style_color()
        return False

    if kind == "amber":
        st = theme.amber_states()
        txt = theme.TAB_TEXT
    elif kind == "pri":
        st = theme.primary_states()
        txt = INK
    else:
        st = theme.secondary_states()
        txt = INK
    imgui.push_style_color(imgui.Col_.button, st["normal"])
    imgui.push_style_color(imgui.Col_.button_hovered, st["hover"])
    imgui.push_style_color(imgui.Col_.button_active, st["pressed"])
    imgui.push_style_color(imgui.Col_.text, txt)
    clicked = imgui.button(f"{label}##{fid}", size)
    # 按下态：内侧 1px 描边环（C2 可检出）
    if imgui.is_item_hovered() and io.mouse_down[0]:
        r0 = imgui.get_item_rect_min()
        r1 = imgui.get_item_rect_max()
        imgui.get_window_draw_list().add_rect(
            imgui.ImVec2(r0.x + 1.0, r0.y + 1.0),
            imgui.ImVec2(r1.x - 1.0, r1.y - 1.0),
            col=_col(theme.ACCENT), rounding=0.0, thickness=1.0)
    if tip and imgui.is_item_hovered():
        imgui.set_tooltip(tip)
    for _ in range(4):
        imgui.pop_style_color()
    return clicked


def _T(zh, en):
    """无 ready 参数处的简/繁/英切换。"""
    from . import lang
    mode = lang.get()
    if mode == "en":
        return en
    if mode == "zh-hant":
        return lang.to_hant(zh)
    return zh


def _panel_origin():
    """面板原点与宽：外置独立窗口（W≈440）时铺满整个窗口；
    inner 回退（窗口=客户区）时固定 440 贴右。比例公式已删。"""
    W = imgui.get_io().display_size.x
    pw = theme.PANEL_W
    if W <= 480.0:
        return 0.0, W
    return W - pw, pw


# ---------------------------------------------------------------- 字体降级

def _font_ready(ctx, root):
    """ctx.font_ready 标志优先；否则读 config/overlay.json ui.font_ready；默认 False。"""
    flag = getattr(ctx, "font_ready", None)
    if flag is not None:
        return bool(flag)
    try:
        raw, err = data.load_json(os.path.join(root, "config", "overlay.json"))
        if err is None and isinstance(raw, dict):
            ui = raw.get("ui") or {}
            return bool(ui.get("font_ready", False))
    except Exception:
        pass
    return False


def _L(ready, zh, en):
    from . import lang
    mode = lang.get()
    if mode == "en":
        return en
    if mode == "zh-hant":
        return lang.to_hant(zh)
    if mode == "zh":
        return zh
    return en if not ready else zh


# ---------------------------------------------------------------- 通用小工具

def _age(path):
    try:
        return time.time() - os.stat(path).st_mtime
    except Exception:
        return None


def _age_str(sec):
    if sec is None:
        return "—"
    if sec < 60:
        return f"{int(sec)}s"
    if sec < 3600:
        return f"{int(sec // 60)}m"
    return f"{int(sec // 3600)}h"


def _normalize_seed(rows):
    """box=[x,y,w,h] -> bbox=[x0,y0,x1,y1]；其余原样。"""
    out = []
    for c in rows or []:
        row = dict(c)
        bbox = row.get("bbox")
        if not bbox and row.get("box"):
            bbox = row["box"]
        norm = data._to_bbox({"bbox": bbox, "box": row.get("box")})
        if norm:
            row["bbox"] = norm
        out.append(row)
    return out


def _ensure_model(ctx, state):
    """按 state.candidates 播种编辑器模型；热重载且无人工改动时重建。"""
    seed = _normalize_seed(getattr(state, "candidates", None))
    sig = json.dumps(
        [(c.get("id"), c.get("bbox"), c.get("confidence")) for c in seed],
        sort_keys=True)
    m = _SESSION["model"]
    if m is None:
        m = EditorModel(seed, calib=getattr(ctx, "geo", None))
        _SESSION["model"] = m
        _SESSION["sig"] = sig
    elif sig != _SESSION["sig"]:
        if not any(c.get("manual") for c in m.candidates):
            m = EditorModel(seed, calib=getattr(ctx, "geo", None))
            _SESSION["model"] = m
            _SESSION["sig"] = sig
    return m


def _io_mouse():
    io = imgui.get_io()
    return (io.mouse_pos.x, io.mouse_pos.y,
            bool(io.mouse_down[0]), bool(io.mouse_down[1]), io.mouse_wheel)


# ================================================================ 主入口

def draw_panel(ctx, state):
    """PANEL 主绘制入口（签名固定）。"""
    if imgui is None:
        return
    root = getattr(state, "root", ".") or "."
    _SESSION["_root"] = root
    ready = _font_ready(ctx, root)
    io = imgui.get_io()
    W, H = io.display_size.x, io.display_size.y
    # 通知 HUD 层面板处于打开态（C9：落进面板矩形的标注跳过）；0.5s 新鲜度失效
    from . import draw as _hud_draw
    _hud_draw.mark_panel_open()
    px, panel_w = _panel_origin()

    # ---- 实底底板（圆角 8，alpha 0.92），内容裁进底板 ----
    # 关键：底板必须画在 BACKGROUND draw list，先于窗口内容（文字）落色；
    # 若画在 foreground list，半透明底板会在文字之上再叠一层，把白字压暗到 ~40。
    dl = imgui.get_background_draw_list()
    if not _SESSION.get("_bg_col_logged"):
        _SESSION["_bg_col_logged"] = True
        ctx.log(f"COLOR selfcheck PANEL_BG col="
                f"{PANEL_BG[0]:.3f},{PANEL_BG[1]:.3f},{PANEL_BG[2]:.3f},"
                f"{PANEL_BG[3]:.3f} alpha>=0.97; panel_w={panel_w:.0f} "
                f"px={px:.0f} W={W:.0f}")
    dl.add_rect_filled(imgui.ImVec2(px, 0.0), imgui.ImVec2(px + panel_w, H),
                        col=_col(PANEL_BG), rounding=8.0)
    dl.add_rect(imgui.ImVec2(px, 0.0), imgui.ImVec2(px + panel_w, H),
                col=_col(PANEL_BORDER), rounding=8.0, thickness=1.0)

    flags = (imgui.WindowFlags_.no_title_bar | imgui.WindowFlags_.no_resize |
             imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_collapse |
             imgui.WindowFlags_.no_scrollbar | imgui.WindowFlags_.no_background |
             imgui.WindowFlags_.no_nav_focus)
    imgui.set_next_window_pos(imgui.ImVec2(px, 0.0))
    imgui.set_next_window_size(imgui.ImVec2(panel_w, H))
    # 全局正文提亮：默认 Col_.text 偏暗，整窗推近白 INK
    imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(*INK))
    imgui.begin("clashlab_panel", None, flags)

    _tab_row(ctx, state, ready, px, panel_w)
    _status_row(ctx, state, root, ready, px, panel_w)
    _engine_row(ctx, state, ready, px, panel_w)

    # P0-1：数据目录缺失 -> 面板中文提示条（禁只在 stderr 打英文栈）。
    if not data.has_data(root):
        # C5：琥珀提示条独占一行（112..160），内容栈由 _content_top 下移，
        # 不再压住「刷新情报」等首行控件；六字「未找到数据目录」完整可见。
        warn_y = STACK_TOP
        dl.add_rect_filled(imgui.ImVec2(px + PAD, warn_y),
                            imgui.ImVec2(px + panel_w - PAD, warn_y + WARN_BAR_H),
                            col=_col((0.32, 0.24, 0.08, 0.95)), rounding=6.0)
        dl.add_rect(imgui.ImVec2(px + PAD, warn_y),
                    imgui.ImVec2(px + panel_w - PAD, warn_y + WARN_BAR_H),
                    col=_col(theme.ACCENT), rounding=6.0, thickness=1.0)
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + 10.0, warn_y + 8.0))
        imgui.text_colored(imgui.ImVec4(*theme.ACCENT),
                           "未找到数据目录，请把 config/ 与 out/ 放在 exe 同级")
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + 10.0, warn_y + 27.0))
        imgui.text_colored(imgui.ImVec4(*GREY),
                           "（也可放到 %LOCALAPPDATA%\\ClashOverlay）")

    # 内容裁进底板矩形，超出不画
    imgui.push_clip_rect(imgui.ImVec2(px, 0.0),
                         imgui.ImVec2(px + panel_w, H), True)
    page = getattr(state, "page", PAGE_RESEARCH) or PAGE_RESEARCH
    if page == PAGE_RESEARCH:
        _draw_research(ctx, state, root, ready, panel_w, px, H)
    elif page == PAGE_LAYOUT:
        _draw_layout(ctx, state, root, ready, panel_w, px, H)
    elif page == PAGE_COLLECT:
        _draw_collect(ctx, state, root, ready, panel_w, px, H)
    else:
        _draw_setting(ctx, state, root, ready, panel_w, px, H)
    imgui.pop_clip_rect()

    # ---- PROBE 调试块（C10）：开关 theme.PROBE_ENABLED（env CLASH_PROBE=1），默认关。
    # 仅开发自检用；发布帧不画任何探针块。
    if theme.PROBE_ENABLED:
        dlp = imgui.get_foreground_draw_list()
        dlp.add_rect_filled(imgui.ImVec2(px + 8.0, H - 40.0),
                            imgui.ImVec2(px + 90.0, H - 12.0),
                            col=_col((0.0, 0.0, 0.0, 0.85)), rounding=3.0)
        dlp.add_text(imgui.ImVec2(px + 12.0, H - 36.0), _col(INK), "PROBE 123")

    imgui.end()
    imgui.pop_style_color()  # 与第 199 行 Col_.text=INK 配对，防跨帧泄漏


# ---------------------------------------------------------------- 引擎模式带

def _engine_row(ctx, state, ready, px, panel_w):
    """y=74 一条：本地模式 / 大模型模式 两个按钮 + 右侧当前引擎状态。

    注意：这一条是页签之下、内容栈之上；STACK_TOP 已随之下移到 112，
    任何页面内容都不许回画到 74~102 这一段（叠字就是这么来的。
    """
    avail_w = panel_w - 2 * PAD
    engine = tactics.SEL.get("engine", ENGINE_LOCAL)
    bw = (avail_w - GAP) / 2.0
    # v6-C8：模式改名 + 各加一行 10px 灰字说明差别（按钮下 y=102，STACK_TOP=112）
    captions = {
        ENGINE_LOCAL: _L(ready, "规则引擎本地算威胁，不联网", "Local rule engine, offline"),
        ENGINE_LLM: _L(ready, "联网调大模型出三段战术", "LLM plan generation (online)"),
    }
    for i, (key, zh, en) in enumerate(((ENGINE_LOCAL, "离线分析（本地）", "Local"),
                                       (ENGINE_LLM, "AI 生成策略", "LLM"))):
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + i * (bw + GAP), 72.0))
        active = engine == key
        if _btn(_L(ready, zh, en), imgui.ImVec2(bw, 26.0),
                kind="pri" if active else "sec", key=f"eng_{key}"):
            tactics.SEL["engine"] = key
            ctx.log(f"engine -> {key}")
        # 10px 灰字说明（不可点，仅文字）：按钮 72..98，说明落在 100..110，不压按钮
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + i * (bw + GAP), 100.0))
        imgui.text_colored(imgui.ImVec4(*SUBTLE), captions[key])


# ---------------------------------------------------------------- 标签条（只显示中文）

def _tab_row(ctx, state, ready, px, panel_w):
    """标签条：4 个等宽按钮，显式坐标排布（依赖 same_line 自动宽度会在 4 个时换行叠字）。"""
    tabs = [
        (PAGE_RESEARCH, _L(ready, "研究", "Research")),
        (PAGE_LAYOUT, _L(ready, "阵型", "Layout")),
        (PAGE_COLLECT, _L(ready, "采集", "Capture")),
        (PAGE_SETTING, _L(ready, "设置", "Settings")),
    ]
    LANGS = (("zh", "中"), ("zh-hant", "繁"), ("en", "EN"))
    LANG_W, LANG_GAP = 27.0, 4.0
    lang_reserve = len(LANGS) * LANG_W + (len(LANGS) - 1) * LANG_GAP + 8.0
    avail_w = panel_w - 2 * PAD - lang_reserve
    bw = (avail_w - GAP * (len(tabs) - 1)) / len(tabs)
    for i, (key, label) in enumerate(tabs):
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + i * (bw + GAP), 12.0))
        active = getattr(state, "page", PAGE_RESEARCH) == key
        if active and not _SESSION.get("_tab_col_logged"):
            _SESSION["_tab_col_logged"] = True
            ctx.log(f"COLOR selfcheck TAB_SEL col="
                    f"{theme.ACCENT[0]:.3f},{theme.ACCENT[1]:.3f},"
                    f"{theme.ACCENT[2]:.3f},{theme.ACCENT[3]:.3f} "
                    f"(amber #E8A33D, text={theme.TAB_TEXT})")
        if _btn(label, imgui.ImVec2(bw, 26.0),
                kind="amber" if active else "sec", key=f"tab_{key}"):
            ctx.set_page(key)
    # 语言切换：标签条最右侧三个小钮（任何页都可见）
    _root = _SESSION.get("_root") or "."
    lang.ensure_loaded(_root)
    cur = lang.get()
    lx0 = px + panel_w - PAD - len(LANGS) * LANG_W - (len(LANGS) - 1) * LANG_GAP
    for i, (mode, lab) in enumerate(LANGS):
        imgui.set_cursor_screen_pos(imgui.ImVec2(lx0 + i * (LANG_W + LANG_GAP), 12.0))
        if _btn(lab, imgui.ImVec2(LANG_W, 26.0), kind="sec",
                active=(cur == mode or (mode == "zh" and cur == "auto")), key=f"lang_{mode}"):
            try:
                lang.set(_root, mode)
            except Exception:
                pass


# ---------------------------------------------------------------- 状态角标

def _text_right(text, rgba, px, panel_w, y):
    """右对齐单行文字：先算宽再定位，避免长串撞到左边内容。"""
    w = imgui.calc_text_size(text).x
    imgui.set_cursor_screen_pos(
        imgui.ImVec2(px + panel_w - PAD - w, y))
    imgui.text_colored(imgui.ImVec4(*rgba), text)


def _status_row(ctx, state, root, ready, px, panel_w):
    live = bool(getattr(state, "live", False))
    live_txt = _L(ready, "运行", "Live") if live else _L(ready, "待命", "Dry run")
    # v6-C7：删掉 study/cand/farm 英文时效行（阻断项），右栏只留中文化
    # 「阵型 已加载 · 候选 N」；候选数读 layout_candidates.json，失败按 0。
    cand_n = 0
    try:
        cand_doc, _err = data.load_json(os.path.join(
            root, "out", "overlay", "layout_candidates.json"))
        if isinstance(cand_doc, list):
            cand_n = len(cand_doc)
        elif isinstance(cand_doc, dict):
            cand_n = len(cand_doc.get("candidates") or cand_doc.get("items") or [])
    except Exception:
        cand_n = 0
    study_png = getattr(state, "study_png", None)
    loaded = bool(getattr(state, "layout", None) or getattr(state, "Layout", None))
    right = _L(ready, f"阵型 {'已加载' if loaded else '未加载/点采集'} · 候选 {cand_n}",
               f"layout {'loaded' if loaded else 'none'} · cand {cand_n}")
    # 左：live 角标（暖黄）；右：中文状态（正文色），各自定位，不互相挤
    # P3b-1：布局已加载时，右栏追加防御评分（无布局保持原样）
    try:
        from . import score_card as _score_card
        right += _score_card.status_suffix(
            _score_card.card_from_layout(getattr(state, "Layout", None)))
    except Exception:
        pass
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, 48.0))
    imgui.text_colored(imgui.ImVec4(*theme.ACCENT), _L(ready, f"面板 实时={live_txt}", f"Panel · {live_txt}"))
    _text_right(right, INK, px, panel_w, 48.0)


# ================================================================ 研究页
# 垂直栈（从上到下，固定 GAP=8；任意 H∈[561,1080] 不重叠、不裁切）：
#   画布(120..420) → 筛选行(26) → 候选列表(48..120) → 冻结行(28) → 来源行(26)
# 画布加上限 420：1080 下不再拉到 768；空间紧张先缩列表，绝不压行高。

CANVAS_MIN, CANVAS_MAX = 120.0, 420.0
LIST_MIN, LIST_MAX = 48.0, 120.0
FILTER_H, FREEZE_H, SOURCE_H = 26.0, BTN_H, 26.0
# 84 处原本是内容起点；模式带占 74~102，起点统一下移到 112
STACK_TOP = 112.0
WARN_BAR_H = 48.0  # C5：缺数据琥珀提示条独占一行高度，内容栈随之下移


def _content_top(root):
    """C5：缺数据目录时琥珀提示条独占一行（112..160），内容栈下移 48px，
    不再压住「刷新情报」等首行控件；数据正常时回到 STACK_TOP。"""
    if not data.has_data(root):
        return STACK_TOP + WARN_BAR_H
    return STACK_TOP


def _doc_cached(root, ttl=1.5):
    """本地情报按 ttl 缓存，热重载后最多 1.5s 自动跟上；每帧不读盘、不做 CV。"""
    now = time.time()
    if (_SESSION["doc"] is None or _SESSION["doc_root"] != root
            or now - _SESSION["doc_t"] > ttl):
        _SESSION["doc"] = tactics.load_local(root)
        _SESSION["doc_root"] = root
        _SESSION["doc_t"] = now
    return _SESSION["doc"]


def _draw_research(ctx, state, root, ready, panel_w, px, H):
    """研究页 = 引擎模式页：本地模式 / 大模型模式 二选一。"""
    engine = tactics.SEL.get("engine", ENGINE_LOCAL)
    if engine == ENGINE_LLM:
        _draw_llm(ctx, state, root, ready, panel_w, px, H)
    else:
        _draw_local(ctx, state, root, ready, panel_w, px, H)


# ---------------------------------------------------------------- 本地模式

def _draw_local(ctx, state, root, ready, panel_w, px, H):
    """本地模式：列出本地规则引擎算出的重要防御，点按钮切换 HUD 聚焦。"""
    avail_w = panel_w - 2 * PAD
    doc = _doc_cached(root)
    rows = doc.get("rows") or []
    # 顶部固定栈（标签/状态/引擎按钮+两行说明）约占 content_top+50；
    # 本地面板从说明行下方开始，避免「刷新情报/统计」压住引擎说明（实机重叠）。
    y = _content_top(root) + 56.0

    # ---- 顶行：刷新按钮（左）+ 统计（右对齐）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "刷新情报", "Refresh intel"), imgui.ImVec2(96.0, 26.0), key="refresh"):
        _SESSION["doc"] = tactics.load_local(root)
        _SESSION["doc_root"] = root
        _SESSION["doc_t"] = time.time()
        ctx.log("local: 情报已刷新")
    cover = doc.get("core_cover_dps")
    stat = f"{len(rows)} 栋"
    if cover:
        stat += f" · 核心 {int(cover)} dps"
    _text_right(stat, SUBTLE, px, panel_w, y + 5.0)
    y += 26.0 + GAP

    # P3b-3：布局弱点两行明细（大本营偏心 / 对空或对地覆盖），无布局时不留空
    _flines = _score_lines(state)[:2]
    if _flines:
        for _i, _ln in enumerate(_flines):
            imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y + _i * 18.0))
            imgui.text_colored(imgui.ImVec4(*GREY), str(_ln)[:46])
        y += 18.0 * len(_flines) + 4.0

    # P3c-3：2D 推演摘要行（缓存命中；无数据显示「推演：无数据」）
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text_colored(imgui.ImVec4(*SUBTLE), _sim_line(state))
    y += 20.0
    imgui.text_colored(imgui.ImVec4(*SUBTLE), _strategy_line(state))
    y += 20.0
    imgui.text_colored(imgui.ImVec4(*SUBTLE), _buildings_line(state))
    y += 20.0
    imgui.text_colored(imgui.ImVec4(*SUBTLE), _opponent_line(state))
    y += 20.0

    # ---- 重要防御行（整行可点；选中=2px 琥珀左条+底板提亮，与 rank 解耦；C3/C6）----
    # P1-4 720 竖向预算：列表按可用高度伸缩，吃满到状态栏上方，不再只按行数收缩
    # 留下大片空白；563 短高下由 avail 自然收小，不崩。空数据给最小 48px。
    avail = (H - 44.0) - y - 44.0  # 让位选中详情两行；空数据也拉伸，不留底部空白
    list_h = max(48.0, avail)
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.begin_child("imp_list", imgui.ImVec2(avail_w, list_h),
                      imgui.ChildFlags_.borders)
    if not rows:
        # v9-⑥：本地模式无数据 -> 「未加载阵型」+ 自动采集按钮（离线只置位请求，
        # 真抓帧分析留实机）
        imgui.text_colored(imgui.ImVec4(*GREY),
                           _L(ready, "未加载阵型：点下方按钮自动采集当前基地",
                              "No layout loaded - press Auto-capture"))
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y + 34.0))
        if _btn(_L(ready, "自动采集", "Auto-capture"),
                imgui.ImVec2(120.0, 26.0), kind="pri", key="auto_capture",
                tip="抓取当前游戏画面并自动检测阵型（需要雷电窗口在前台）"):
            try:
                ctx.request_data_prep()  # v9-⑥闭环：置位 -> 主循环查表/抓帧+detect 消费
                ctx.request_study({"auto": True})
                ctx.log("local: 自动采集请求已置位（表优先，无表抓帧+detect）")
            except Exception as e:
                ctx.log(f"auto-capture request fail: {e}")
    bgdl = imgui.get_background_draw_list()
    fg = imgui.get_foreground_draw_list()
    child_top = y
    for i, r in enumerate(rows):
        sel = (i == int(tactics.SEL.get("idx", 0)))
        row_y = imgui.get_cursor_pos().y
        # 行底/选中条画在背景层（屏幕坐标，位于窗口文字之下）：子窗内 window draw list
        # 在本后端不提交。选中=2px 琥珀左竖条 + 底板提亮一档（C3），与 rank 无关。
        sy = child_top + 6.0 + i * 30.0
        bgdl.add_rect_filled(
            imgui.ImVec2(px + PAD, sy),
            imgui.ImVec2(px + PAD + avail_w, sy + 26.0),
            col=_col(theme.SEL_ROW_BG if sel else theme.ROW_BG), rounding=4.0)
        if sel:
            if not _SESSION.get("_sel_col_logged"):
                _SESSION["_sel_col_logged"] = True
                ctx.log(f"COLOR selfcheck SEL_BAR col="
                        f"{theme.SEL_BAR[0]:.3f},{theme.SEL_BAR[1]:.3f},"
                        f"{theme.SEL_BAR[2]:.3f},{theme.SEL_BAR[3]:.3f} "
                        f"SEL_ROW_BG={theme.SEL_ROW_BG}; rank 不参与选中")
            # v6-C9 重修：左竖条画 6px（两侧各 1px 抗锯齿，纯 #E8A33D 核心 = 4px）
            bgdl.add_rect_filled(
                imgui.ImVec2(px + PAD, sy),
                imgui.ImVec2(px + PAD + 6.0, sy + 26.0),
                col=_col(theme.SEL_BAR), rounding=0.0)
        # rank 只用前缀符号+色（▲/◆/○，三档实色），不铺底、不随选中变红/蓝
        rank = int(r.get("rank", 1))
        glyph = theme.RANK_GLYPH.get(rank, "○")
        rank_col = {3: theme.RANK_R3, 2: theme.RANK_R2, 1: theme.RANK_R1}.get(rank, theme.RANK_R1)
        label = f"{r['name']}  格({r['tile'][0]:.0f},{r['tile'][1]:.0f})"
        if r.get("dps"):
            label += f"   {r['dps']} dps"
        if sel:
            # v6-C9：选中字纯白提亮一档 + 伪加粗（同位移 1px 双绘）
            fg.add_text(imgui.ImVec2(px + PAD + 28.0, sy + 3.0),
                        _col((1.0, 1.0, 1.0, 1.0)), label)
            fg.add_text(imgui.ImVec2(px + PAD + 29.0, sy + 3.0),
                        _col((1.0, 1.0, 1.0, 1.0)), label)
        else:
            imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + 28.0, sy + 3.0))
            imgui.text_colored(imgui.ImVec4(*INK), label)
        fg.add_text(imgui.ImVec2(px + PAD + 10.0, sy + 3.0), _col(rank_col), glyph)
        # invisible_button 承接整行点击（不画填充、不居中文字）
        imgui.set_cursor_pos(imgui.ImVec2(0.0, row_y))
        if imgui.invisible_button(f"loc_row_{i}", imgui.ImVec2(avail_w - 12.0, 26.0)):
            tactics.SEL["idx"] = i
            ctx.log(f"local: 聚焦 {r['name']} 格{r['tile']}")
        imgui.dummy(imgui.ImVec2(0.0, 6.0))
    imgui.end_child()
    y += list_h + GAP

    # ---- 选中详情（两行，固定高度，不与底部状态栏重叠）----
    cur = tactics.selected(doc)
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if cur:
        edge = f"距边 {cur['edge_dist']} 格" if cur.get("edge_dist") is not None else _T("距边未知", "edge: unknown")
        imgui.text_colored(imgui.ImVec4(*INK),
                           _L(ready, f"聚焦 {cur['name']} · {cur['dps']} dps · {edge}",
                              f"Focus {cur['name']} · {cur['dps']} dps · {edge}"))
        imgui.text_colored(imgui.ImVec4(*GREY),
                           _L(ready, "HUD 上该建筑已加粗高亮，其余弱化",
                              "Highlighted on HUD (others dimmed)"))
    else:
        imgui.text_colored(imgui.ImVec4(*GREY),
                           _L(ready, "无可标注目标", "Nothing to annotate"))

    _bottom_status(px, H, None, ready, PAGE_RESEARCH, avail_w,
                   extra=f"本地 · {doc.get('source') or '无数据'}")


# ---------------------------------------------------------------- 大模型模式

def _draw_llm(ctx, state, root, ready, panel_w, px, H):
    """大模型模式：选目标 -> 后台请求 -> 滚动显示三段式策略。"""
    avail_w = panel_w - 2 * PAD
    doc = _doc_cached(root)
    job = tactics.job()
    if _SESSION["plan"] is None or _SESSION["plan_t"] < (doc.get("_t") or 0):
        if job["state"] in ("done", "fallback") and job.get("text"):
            # v2 结构化字段（phases/threats/win_condition）从已写盘的 plan.json 补回，
            # 供「路线图阶段」块渲染；job 载荷只带 text，不带结构化数据
            _full = tactics.load_plan(root) or {}
            _SESSION["plan"] = {"text": job["text"], "model": job["model"],
                                "elapsed": job["elapsed"], "goal": job["goal"],
                                "err": job.get("err", ""),
                                "fallback": bool(job.get("fallback")),
                                "phases": _full.get("phases"),
                                "threats": _full.get("threats"),
                                "win_condition": _full.get("win_condition")}
        else:
            _SESSION["plan"] = _SESSION["plan"] or tactics.load_plan(root)
    plan = _SESSION["plan"] or {}
    y = _content_top(root)

    # ---- 目标选择（4 个小按钮，选中=主绿，未选=灰；统一三态）----
    # 注意：text() 后直接 same_line 会让光标跳回上一个 item（按钮）所在行，
    # 导致兵种下拉盖到目标行（审计 R1）；改用显式定位按钮起点。
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, "目标", "Goal"))
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + 56.0, y + 2.0))
    for g in tactics.GOALS:
        active = _SESSION["goal"] == g
        st = theme.primary_states() if active else theme.secondary_states()
        imgui.push_style_color(imgui.Col_.button, st["normal"])
        imgui.push_style_color(imgui.Col_.button_hovered, st["hover"])
        imgui.push_style_color(imgui.Col_.button_active, st["pressed"])
        imgui.push_style_color(imgui.Col_.text, INK)
        if imgui.small_button(g):
            _SESSION["goal"] = g
        for _ in range(4):
            imgui.pop_style_color()
        imgui.same_line(spacing=6.0)
    y += 26.0 + GAP

    # ---- 兵种 / 装备下拉（LLM 透传给 KB 检索打分 army+2/equipment+3；
    # 不选=空，保持原行为；选项只收 KB 卡面实有 id，见 tactics.ARMY/EQUIPMENT_OPTIONS）----
    for key, label, opts in (
            ("army", _L(ready, "兵种", "Army"), tactics.ARMY_OPTIONS),
            ("equipment", _L(ready, "装备", "Equipment"), tactics.EQUIPMENT_OPTIONS)):
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
        imgui.text(label)
        # 同上：不用 same_line，显式把下拉放到本行右侧（审计 R1）
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + 56.0, y + 2.0))
        cur = tactics.SEL.get(key, "")
        items = [("", "（不选）")] + opts
        cur_i = next((i for i, (_id, _lb) in enumerate(items) if _id == cur), 0)
        imgui.push_item_width(180.0)
        if imgui.begin_combo(f"##{key}", items[cur_i][1]):
            for i, (_id, lb) in enumerate(items):
                clicked, _sel = imgui.selectable(lb, i == cur_i)
                if clicked:
                    tactics.SEL[key] = _id
                    ctx.log(f"llm {key} -> {_id or '（空）'}")
            imgui.end_combo()
        imgui.pop_item_width()
        y += 26.0 + GAP

    # ---- v5 chip 开关：威胁 1-5 / 路线 1-6（仅 PANEL 可点；HUD 只显示不可点角标）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    for key, txt in (("show_threats", "威胁 1-5"), ("show_route", "路线 1-6")):
        on = bool(tactics.SEL.get(key, True))
        st = theme.primary_states() if on else theme.secondary_states()
        imgui.push_style_color(imgui.Col_.button, st["normal"])
        imgui.push_style_color(imgui.Col_.button_hovered, st["hover"])
        imgui.push_style_color(imgui.Col_.button_active, st["pressed"])
        imgui.push_style_color(imgui.Col_.text, INK)
        if imgui.small_button(_L(ready, txt, txt)):
            tactics.SEL[key] = not on
            ctx.log(f"llm marks {key} -> {tactics.SEL[key]}")
        for _ in range(4):
            imgui.pop_style_color()
        imgui.same_line(spacing=GAP)
    y += 26.0 + GAP

    # ---- 生成按钮（主绿；运行中=等待区：大字「正在生成… 已 Ns」+ 真比例进度条；
    # 兜底态=琥珀满格 + 「AI 生成失败，已切换本地分析」）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    running = job["state"] == "run"
    fallback = job["state"] == "fallback"
    if running or fallback:
        fg = imgui.get_foreground_draw_list()
        block_h = 52.0
        budget = tactics.FALLBACK_BUDGET
        if running:
            # now 与比例同一只时钟：job.now 由 t0（perf_counter）实时推得
            now_s = float(job.get("now", 0.0) or 0.0)
            ratio = min(1.0, max(0.0, now_s / budget))
            head = _L(ready, f"正在生成… 已 {now_s:.0f}s",
                      f"generating… {now_s:.0f}s")
            head_col = INK
            bar_col = theme.ACCENT
        else:
            # 兜底触发即满格（ratio=1.0）：满格与兜底同帧，不许满格后还继续等
            now_s = float(job.get("elapsed", 0.0) or 0.0)
            ratio = 1.0
            head = _L(ready, "AI 生成失败，已切换本地分析",
                      "AI failed - switched to local analysis")
            head_col = theme.WARN
            bar_col = theme.ACCENT
        fg.add_rect_filled(imgui.ImVec2(px + PAD, y),
                           imgui.ImVec2(px + PAD + avail_w, y + block_h),
                           col=_col((0.075, 0.102, 0.141, 1.0)), rounding=6.0)
        fg.add_rect(imgui.ImVec2(px + PAD, y),
                    imgui.ImVec2(px + PAD + avail_w, y + block_h),
                    col=_col(theme.ACCENT), rounding=6.0, thickness=1.0)
        fg.add_text(imgui.ImVec2(px + PAD + 14.0, y + 9.0),
                    _col(head_col), head)
        # 真比例进度条：draw 层实心矩形（填充段/空槽段各一，无字形抗锯齿缝），
        # 填充宽 = ratio * 轨道宽，像素比与理论比一致；同一只时钟推 now 与 ratio。
        x0 = px + PAD + 14.0
        track_w = avail_w - 28.0
        bar_h = 10.0
        by = y + 30.0
        # 空槽段（轨道底）
        fg.add_rect_filled(imgui.ImVec2(x0, by),
                            imgui.ImVec2(x0 + track_w, by + bar_h),
                            col=_col((0.130, 0.161, 0.200, 1.0)), rounding=0.0)
        # 填充段（实心，宽=ratio*轨道宽）
        fw = ratio * track_w
        if fw > 0.5:
            fg.add_rect_filled(imgui.ImVec2(x0, by),
                               imgui.ImVec2(x0 + fw, by + bar_h),
                               col=_col(bar_col), rounding=0.0)
        y += block_h + GAP
    else:
        if _btn(_L(ready, "生成策略", "Generate plan"), imgui.ImVec2(140.0, BTN_H),
                kind="pri", key="gen",
                tip="需要先加载阵型/候选；LLM 模式还需要 API 配置"):
            sel = tactics.selected(doc)
            tactics.start_plan(
                root, doc, goal=_SESSION["goal"], sel=sel,
                army=tactics.SEL.get("army") or None,
                equipment=tactics.SEL.get("equipment") or None)
            ctx.log(f"llm: 请求策略 goal={_SESSION['goal']} sel={(sel or {}).get('name')} "
                    f"army={tactics.SEL.get('army') or '-'} "
                    f"equipment={tactics.SEL.get('equipment') or '-'}")
        meta = plan.get("model") or ""
        if meta:
            _text_right(f"{meta} · {plan.get('elapsed', 0)}s", GREY,
                        px, panel_w, y + 9.0)
        y += BTN_H + GAP

    # ---- 策略区：散文 + 路线图阶段 + 威胁清单，合并进一个自然流可滚动子窗 ----
    # 旧版分块+手动 set_cursor_pos 不登记内容高度，子窗不出滚动条，底边把行横切成
    # 半截字。改为 ImGui 自然流排版，内容超高时子窗自动出滚动条；可视区只渲染完整
    # 行，底边落在行中间时该行不画（滚到底自然可见），不留半截字。
    _has_v2 = bool((plan or {}).get("phases") or (plan or {}).get("threats"))
    scroll_h = max(80.0, (H - 44.0) - y - 8.0)
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.begin_child("plan_scroll", imgui.ImVec2(avail_w, scroll_h),
                      imgui.ChildFlags_.borders)
    if job["state"] == "fail" and job.get("err"):
        imgui.text_colored(imgui.ImVec4(*RED),
                           _L(ready, "生成失败：", "Generation failed: ") + str(job["err"])[:160])
    if job["state"] == "done" and job.get("text"):
        _full = tactics.load_plan(root) or {}
        plan = {"text": job["text"], "model": job["model"],
                "elapsed": job["elapsed"], "goal": job["goal"],
                "phases": _full.get("phases"),
                "threats": _full.get("threats"),
                "win_condition": _full.get("win_condition")}
        _SESSION["plan"] = plan
    # ③ 兜底态：琥珀提示条「AI 生成失败，已切换本地分析」+ 原因小字，正文接本地规则文本
    if job["state"] == "fallback" or (plan or {}).get("fallback"):
        imgui.text_colored(imgui.ImVec4(*YELLOW),
                           _L(ready, "AI 生成失败，已切换本地分析",
                              "AI failed - switched to local analysis"))
        reason = job.get("err") or (plan or {}).get("reason") or ""
        if reason:
            imgui.text_colored(imgui.ImVec4(*GREY), f"原因：{str(reason)[:120]}")
    body = _strip_dupe(_zh_body((plan or {}).get("text") or ""))
    if body:
        # text_wrapped 按子窗宽度自动折行；PushTextWrapPos 收窗口本地区标
        imgui.push_text_wrap_pos(avail_w - 10.0)
        imgui.text_wrapped(body)
        imgui.pop_text_wrap_pos()
    elif job["state"] != "run":
        imgui.text_colored(
            imgui.ImVec4(*GREY),
            _L(ready, "点“生成策略”让大模型读当前情报给三段战术。",
               "Press Generate plan for a three-part plan."))

    # ---- v2 路线图阶段 + 威胁清单（phases 命中才画；旧 v5 无 phases 不显示）----
    # 阶段色直接取 plan_render.PHASE_COLORS，不在此另调色板。
    # 整行裁剪：行高放不进可视底界时，把 clip 空矩形压到行顶（y1 <= 底-1 才画），
    # 该行整行不画、不许底边落行中间画半截字；行仍提交进布局，滚动 extent 保留，
    # 滚下去整行可见。
    if _has_v2:
        from .plan_render import PHASE_COLORS
        child_bottom = scroll_h - 10.0  # 子窗本地可视底（留 padding）
        wpos = imgui.get_window_pos()

        def _row(h, draw_row):
            cy = imgui.get_cursor_pos().y
            if cy + h <= child_bottom + 1.0:
                draw_row()
                return
            imgui.push_clip_rect(
                imgui.ImVec2(wpos.x, wpos.y + cy),
                imgui.ImVec2(wpos.x + avail_w, wpos.y + cy),
                False)
            draw_row()
            imgui.pop_clip_rect()

        imgui.dummy(imgui.ImVec2(0.0, 6.0))
        _row(20.0, lambda: imgui.text_colored(
            imgui.ImVec4(*GREY), _L(ready, "路线图阶段", "Phases")))
        for i, ph in enumerate((plan or {}).get("phases") or []):
            col = PHASE_COLORS[i % len(PHASE_COLORS)]
            col1 = tuple(c / 255.0 for c in col) + (1.0,)
            t0 = float(ph.get("t_start", 0) or 0)
            t1 = float(ph.get("t_end", 0) or 0)
            name = str(ph.get("name") or "")
            _row(20.0, lambda: (
                imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(*col1)),
                imgui.text(f"{ph.get('i', i + 1)}. {name}  {t0:.0f}-{t1:.0f}s"),
                imgui.pop_style_color()))
            purpose = str(ph.get("purpose") or "")
            if purpose:
                _row(38.0, lambda: (
                    imgui.push_text_wrap_pos(avail_w - 14.0),
                    imgui.text_colored(imgui.ImVec4(*GREY), purpose),
                    imgui.pop_text_wrap_pos()))
            imgui.spacing()
        threats = (plan or {}).get("threats") or []
        if threats:
            _row(20.0, lambda: imgui.text_colored(
                imgui.ImVec4(*RED), _L(ready, "威胁清单", "Threats")))
            for th in threats:
                typ = tactics.NAME_ZH.get(th.get("type"), th.get("type") or "")
                why = str(th.get("why") or "")
                _row(38.0, lambda: (
                    imgui.push_text_wrap_pos(avail_w - 14.0),
                    imgui.text_colored(imgui.ImVec4(*INK), f"· {typ} · {why}"),
                    imgui.pop_text_wrap_pos()))
                imgui.spacing()
    imgui.end_child()

    _bottom_status(px, H, None, ready, PAGE_RESEARCH, avail_w,
                   extra=f"大模型 · {_SESSION['goal']}")


def _draw_layout(ctx, state, root, ready, panel_w, px, H):
    m = _ensure_model(ctx, state)
    avail_w = panel_w - 2 * PAD

    # 内容底界 H-44：状态栏独立一行在 H-26，栈底与状态栏之间留 ≥18px
    avail = (H - 44.0) - _content_top(root)
    fixed = FILTER_H + FREEZE_H + SOURCE_H + GAP * 3
    # 列表弹性：优先 120，最少 48
    list_h = min(LIST_MAX, max(LIST_MIN, avail - fixed - GAP * 2 - CANVAS_MAX))
    # 画布弹性：吃剩余空间，夹在 [120,420]
    canvas_h = min(CANVAS_MAX, max(CANVAS_MIN,
                                   avail - fixed - GAP * 2 - list_h))

    y = _content_top(root)
    canvas_rect = (px + PAD, y, avail_w, canvas_h)
    _SESSION["canvas_rect"] = canvas_rect
    _editor_canvas(ctx, state, m, ready, canvas_rect)
    y += canvas_h + GAP

    # ---- 筛选行（标签 + 全部/≥0.3/≥0.5/≥0.7 按钮组，8px 间距；三态统一）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, "候选筛选", "Filter"))
    imgui.same_line(spacing=GAP)
    for v, t in [(0.0, _L(ready, "全部", "All")),
                 (0.3, "≥0.3"), (0.5, "≥0.5"), (0.7, "≥0.7")]:
        active = _SESSION["threshold"] == v
        st = theme.primary_states() if active else theme.secondary_states()
        imgui.push_style_color(imgui.Col_.button, st["normal"])
        imgui.push_style_color(imgui.Col_.button_hovered, st["hover"])
        imgui.push_style_color(imgui.Col_.button_active, st["pressed"])
        imgui.push_style_color(imgui.Col_.text, INK)
        if imgui.small_button(t):
            _SESSION["threshold"] = v
        for _ in range(4):
            imgui.pop_style_color()
        imgui.same_line(spacing=GAP)
    # 补框模式开关（筛选行末端，独立小按钮）
    add_label = _L(ready, "退出补框", "Finish boxes") if _SESSION["add_mode"] \
        else _L(ready, "补框模式", "Add box mode")
    st = theme.primary_states() if _SESSION["add_mode"] else theme.secondary_states()
    imgui.push_style_color(imgui.Col_.button, st["normal"])
    imgui.push_style_color(imgui.Col_.button_hovered, st["hover"])
    imgui.push_style_color(imgui.Col_.button_active, st["pressed"])
    imgui.push_style_color(imgui.Col_.text, INK)
    if imgui.small_button(add_label):
        _SESSION["add_mode"] = not _SESSION["add_mode"]
        m.end_drag()
        ctx.log(f"editor: add_mode={_SESSION['add_mode']}")
    for _ in range(4):
        imgui.pop_style_color()
    y += FILTER_H + GAP

    # ---- 候选列表（高度随内容收缩，封顶 120px，不拉满；C6）----
    # 选中=2px 琥珀左条+底板提亮，与 rank/置信度解耦（C3）。
    visible = [c for c in m.sorted_by_confidence()
               if c["confidence"] >= _SESSION["threshold"]]
    list_h = min(LIST_MAX, max(LIST_MIN, 24.0 * len(visible) + 12.0))
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.begin_child("cand_list", imgui.ImVec2(avail_w, list_h),
                      imgui.ChildFlags_.borders)
    bgdl = imgui.get_background_draw_list()
    fg = imgui.get_foreground_draw_list()
    cand_top = y
    for ci, c in enumerate(visible):
        row_y = imgui.get_cursor_pos().y
        sel = bool(c.get("selected"))
        sy = cand_top + 6.0 + ci * 30.0
        # 行底/选中条画在背景层（屏幕坐标）；选中=2px 琥珀左条+提亮（C3，与置信度解耦）
        bgdl.add_rect_filled(
            imgui.ImVec2(px + PAD, sy),
            imgui.ImVec2(px + PAD + avail_w, sy + 26.0),
            col=_col(theme.SEL_ROW_BG if sel else theme.ROW_BG), rounding=4.0)
        if sel:
            # v6-C9 重修：左竖条画 6px（两侧各 1px 抗锯齿，纯 #E8A33D 核心 = 4px）
            bgdl.add_rect_filled(
                imgui.ImVec2(px + PAD, sy),
                imgui.ImVec2(px + PAD + 6.0, sy + 26.0),
                col=_col(theme.SEL_BAR), rounding=0.0)
            fg.add_text(imgui.ImVec2(px + PAD + 10.0, sy + 3.0),
                        _col((1.0, 1.0, 1.0, 1.0)), c["label"])
            fg.add_text(imgui.ImVec2(px + PAD + 11.0, sy + 3.0),
                        _col((1.0, 1.0, 1.0, 1.0)), c["label"])
        # 名称（左，点击选中）；invisible_button 承接，文字左对齐（C3 解耦）
        if not sel:
            imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + 10.0, sy + 3.0))
            imgui.text_colored(imgui.ImVec4(*INK), c["label"])
        imgui.set_cursor_pos(imgui.ImVec2(0.0, row_y))
        if imgui.invisible_button(f"cand_{c['id']}",
                                  imgui.ImVec2(avail_w - 210.0, 24.0)):
            m.select(c["id"])
        imgui.same_line(spacing=8.0)
        # 置信度（次亮色，独立于操作列）
        imgui.text_colored(imgui.ImVec4(*SUBTLE), f"{c['confidence']:.2f}")
        imgui.same_line(spacing=8.0)
        eye = _L(ready, "隐藏", "Hide") if not c.get("hidden") else _L(ready, "显示", "Show")
        st2 = theme.secondary_states()
        imgui.push_style_color(imgui.Col_.button, st2["normal"])
        imgui.push_style_color(imgui.Col_.button_hovered, st2["hover"])
        imgui.push_style_color(imgui.Col_.button_active, st2["pressed"])
        imgui.push_style_color(imgui.Col_.text, INK)
        if imgui.small_button(eye):
            m.toggle_hidden(c["id"])
        for _ in range(4):
            imgui.pop_style_color()
        imgui.same_line(spacing=6.0)
        st3 = theme.secondary_states()
        imgui.push_style_color(imgui.Col_.button, st3["normal"])
        imgui.push_style_color(imgui.Col_.button_hovered, st3["hover"])
        imgui.push_style_color(imgui.Col_.button_active, st3["pressed"])
        imgui.push_style_color(imgui.Col_.text, theme.DANGER)
        if imgui.small_button(_L(ready, "删", "Delete")):
            m.delete(c["id"])
            ctx.log(f"editor: 删除 {c['id']}")
        for _ in range(4):
            imgui.pop_style_color()
        imgui.dummy(imgui.ImVec2(0.0, 6.0))
    imgui.end_child()
    y += list_h + GAP

    # ---- 冻结行（独立一行，按钮 28px；主绿三态；结果提示换行显示，不挤在右侧）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "冻结 layout", "Lock layout"),
            imgui.ImVec2(140.0, BTN_H), kind="pri", key="freeze"):
        source_meta = {
            "image": str(getattr(state, "candidates_png", None)
                         or getattr(state, "study_png", None) or ""),
            "candidates": "out/overlay/layout_candidates.json",
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        res = ctx.freeze_layout(m, source_meta=source_meta,
                                quad=getattr(state, "quad_px", None), grid=44)
        _SESSION["freeze_ok"] = bool(res.get("ok"))
        _SESSION["freeze_msg"] = res.get("message", "")
        _SESSION["freeze_path"] = res.get("current") or res.get("snapshot") or ""
        ctx.log(f"freeze: {res.get('message')}")
    if _SESSION["freeze_ok"] is True:
        imgui.text_colored(imgui.ImVec4(*GREEN), "✓ " + _SESSION["freeze_msg"])
    elif _SESSION["freeze_ok"] is False:
        imgui.text_colored(imgui.ImVec4(*RED), "✗ " + _SESSION["freeze_msg"])
    y += FREEZE_H + GAP

    # ---- 来源行：触发研究按钮（次要灰三态）+ 换行灰字说明 ----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "触发研究", "Run research"),
            imgui.ImVec2(110.0, SOURCE_H), kind="sec", key="run_study",
            tip="后台跑研究报告，完成后自动刷新面板"):
        fn = getattr(ctx, "request_study", None)
        if callable(fn):
            fn({})
            ctx.log("study: requested (background)")
        else:
            ctx.log("study: request_study 未由运行时提供（见 needs_from_a N7）")
    imgui.same_line(spacing=GAP)
    imgui.text_colored(imgui.ImVec4(*GREY),
                       _L(ready, "后台子进程，完成自动刷新", "Runs in background; auto-reloads"))

    try:
        from . import score_card as _score_card
        _extra = _score_card.bottom_text(
            _score_card.card_from_layout(getattr(state, "Layout", None))) or None
    except Exception:
        _extra = None
    _bottom_status(px, H, m, ready, PAGE_LAYOUT, avail_w, extra=_extra)


def _editor_canvas(ctx, state, m, ready, rect):
    """候选图/原图等比缩放显示；点选、拖动、拖角、右键删除、空白新建。"""
    cx, cy, cw, ch = rect
    # 底图：候选 overlay.png 优先；缺失则用研究原图；都没有则纯画布可补框
    base = getattr(state, "candidates_png", None) or getattr(state, "study_png", None)
    meta = (data.image_meta(str(base)) if base else None) or {}
    iw, ih = (meta.get("w") or 1280), (meta.get("h") or 720)
    vt = ViewTransform(iw, ih, ax=cx, ay=cy, aw=cw, ah=ch,
                       render_w=1280.0, render_h=720.0)

    dl = imgui.get_window_draw_list()
    # 画布内底：letterbox 区铺一层略深底，边框提亮
    dl.add_rect_filled(imgui.ImVec2(cx, cy), imgui.ImVec2(cx + cw, cy + ch),
                        col=_col(theme.CANVAS_BG), rounding=6.0)
    dl.add_rect(imgui.ImVec2(cx, cy), imgui.ImVec2(cx + cw, cy + ch),
                col=_col(PANEL_BORDER), rounding=6.0, thickness=1.0)
    if base and os.path.exists(str(base)):
        tex = ctx.texture(str(base), key="editor_base", max_px=int(cw))
        if tex:
            imgui.set_cursor_screen_pos(imgui.ImVec2(vt.off_x, vt.off_y))
            imgui.image(tex, imgui.ImVec2(vt.disp_w, vt.disp_h))
    else:
        # 缺底图参考层：淡网格（每 1/4 一条）+ 居中菱形 + 原点十字，便于定位
        # 中性灰/琥珀，不带蓝紫相（C1）
        grid = _col(theme.GRID_LINE)
        for f in (0.25, 0.5, 0.75):
            gx = cx + cw * f
            gy = cy + ch * f
            dl.add_line(imgui.ImVec2(gx, cy + 4), imgui.ImVec2(gx, cy + ch - 4), grid, 1.0)
            dl.add_line(imgui.ImVec2(cx + 4, gy), imgui.ImVec2(cx + cw - 4, gy), grid, 1.0)
        ccx, ccy = cx + cw / 2.0, cy + ch / 2.0
        hw, hh = cw * 0.38, ch * 0.38
        diamond = _col(theme.ACCENT[:3] + (0.55,))
        dl.add_line(imgui.ImVec2(ccx, ccy - hh), imgui.ImVec2(ccx + hw, ccy), diamond, 1.5)
        dl.add_line(imgui.ImVec2(ccx + hw, ccy), imgui.ImVec2(ccx, ccy + hh), diamond, 1.5)
        dl.add_line(imgui.ImVec2(ccx, ccy + hh), imgui.ImVec2(ccx - hw, ccy), diamond, 1.5)
        dl.add_line(imgui.ImVec2(ccx - hw, ccy), imgui.ImVec2(ccx, ccy - hh), diamond, 1.5)
        # 原点十字
        dl.add_line(imgui.ImVec2(ccx - 8, ccy), imgui.ImVec2(ccx + 8, ccy),
                    _col(theme.SUB[:3] + (0.7,)), 1.5)
        dl.add_line(imgui.ImVec2(ccx, ccy - 8), imgui.ImVec2(ccx, ccy + 8),
                    _col(theme.SUB[:3] + (0.7,)), 1.5)
        dl.add_text(imgui.ImVec2(cx + 10.0, cy + 8.0), _col(SUBTLE),
                    _L(ready, "无底图：网格/菱形为参考层，可直接点选补框",
                       "No base image: grid/diamond is a reference - click to add boxes"))

    # ---- 鼠标交互（全局坐标；ctx.mouse 缺省回退 io） ----
    mouse = ctx.mouse() if hasattr(ctx, "mouse") else _io_mouse()
    mx, my, left, right = mouse[0], mouse[1], mouse[2], mouse[3]
    inside = cx <= mx <= cx + cw and cy <= my <= cy + ch
    rx, ry = vt.panel_to_render(mx, my)
    grab = 10.0 / vt.scale  # 面板 10px -> 渲染坐标

    if left and not _SESSION["prev_left"]:
        if inside:
            if _SESSION["add_mode"]:
                cid, _ = m.hit_test(rx, ry, grab)
                if cid is None:
                    _SESSION["new_rect"] = [rx, ry, rx, ry]
            else:
                m.begin_drag(rx, ry, grab)
    elif left and _SESSION["prev_left"]:
        if _SESSION["new_rect"] is not None:
            _SESSION["new_rect"][2], _SESSION["new_rect"][3] = rx, ry
        else:
            m.drag_to(rx, ry)
    elif not left and _SESSION["prev_left"]:
        m.end_drag()
        nr = _SESSION["new_rect"]
        if nr is not None:
            x0, y0 = min(nr[0], nr[2]), min(nr[1], nr[3])
            x1, y1 = max(nr[0], nr[2]), max(nr[1], nr[3])
            if x1 - x0 > 6 and y1 - y0 > 6:
                m.add([x0, y0, x1, y1], label="手动补框", confidence=0.0)
                ctx.log("editor: 新建补框")
            _SESSION["new_rect"] = None

    if right and not _SESSION["prev_right"] and inside:
        cid, _ = m.hit_test(rx, ry, grab)
        if cid and m.delete(cid):
            ctx.log(f"editor: 删除 {cid}")

    _SESSION["prev_left"] = bool(left)
    _SESSION["prev_right"] = bool(right)

    # ---- 绘制候选框（渲染 -> 面板），框左上角标序号 1..n ----
    thr = _SESSION["threshold"]
    for idx, c in enumerate(m.candidates, start=1):
        if c.get("hidden") or c["confidence"] < thr:
            continue
        r = Rect.from_list(c["bbox"])
        p0 = vt.render_to_panel(r.x0, r.y0)
        p1 = vt.render_to_panel(r.x1, r.y1)
        sel = c.get("selected")
        # 普通框 2px 灰边；选中框 3px 琥珀（唯一强调色，不带绿/蓝旧色）
        line_w = 3.0 if sel else 2.0
        col = _col(theme.ACCENT if sel else theme.SEC_BORDER)
        dl.add_rect(imgui.ImVec2(*p0), imgui.ImVec2(*p1),
                    col=col, rounding=2.0, thickness=line_w)
        for _, (qx, qy) in r.corners().items():
            qp = vt.render_to_panel(qx, qy)
            dl.add_rect_filled(imgui.ImVec2(qp[0] - 3, qp[1] - 3),
                               imgui.ImVec2(qp[0] + 3, qp[1] + 3), col=col)
        # 序号气泡：框左上角深底白字，便于直接点选
        num = f"{idx}"
        ns = imgui.calc_text_size(num)
        nx, ny = p0[0] + 2.0, p0[1] - ns.y - 6.0
        ny = max(cy + 2.0, ny)
        dl.add_rect_filled(imgui.ImVec2(nx - 2.0, ny - 1.0),
                            imgui.ImVec2(nx + ns.x + 5.0, ny + ns.y + 3.0),
                            col=_col(theme.CHIP_BG), rounding=3.0)
        dl.add_text(imgui.ImVec2(nx + 1.0, ny), _col(INK), num)
        if sel or c["confidence"] >= 0.6:
            tag = f"{c['label']} {c['confidence']:.2f}"
            ts = imgui.calc_text_size(tag)
            tx, ty = p0[0] + 4.0, max(cy + 4.0, p1[1] + 4.0)
            # 标签 14px：半透明深底 + 白字，避免压框看不清
            dl.add_rect_filled(imgui.ImVec2(tx - 3.0, ty - 2.0),
                                imgui.ImVec2(tx + ts.x + 6.0, ty + ts.y + 4.0),
                                col=_col(theme.CHIP_BG), rounding=3.0)
            dl.add_text(imgui.ImVec2(tx, ty), _col(INK), tag)

    nr = _SESSION["new_rect"]
    if nr is not None:
        a = vt.render_to_panel(nr[0], nr[1])
        b = vt.render_to_panel(nr[2], nr[3])
        dl.add_rect(imgui.ImVec2(*a), imgui.ImVec2(*b),
                    col=_col(theme.ACCENT), rounding=0.0, thickness=1.5)
    # 注：补框模式开关/操作提示由 _draw_research 的垂直栈绘制，
    # 本函数只负责底图、交互命中与候选框渲染，不在画布下方另画一行（旧版叠字来源）。


# ---------------------------------------------------------------- 底部独立状态栏

def _score_lines(state):
    """P3b-3：布局弱点明细（最多 2 行）；无布局/无数据返回 []。"""
    try:
        from . import score_card as _sc
        return _sc.detail_lines(getattr(state, "Layout", None))
    except Exception:
        return []



_STRATEGY_CACHE = {"key": None, "line": ""}


def _fmt_strategy_info(info):
    """把 prebattle info 里的 strategies 压成一行文案（纯函数，便于测试）。"""
    if not isinstance(info, dict):
        return _T("推荐：无数据", "Recommendation: no data")
    summary = info.get("strategy_summary")
    if summary:
        return "推荐：" + str(summary)[:42]
    recs = info.get("strategies")
    if isinstance(recs, list) and recs and isinstance(recs[0], dict):
        r0 = recs[0]
        return "推荐：" + ("%s（%s）" % (r0.get("name"), r0.get("reason")))[:42]
    return _T("推荐：无数据", "Recommendation: no data")


def _strategy_line(state):
    """v11-战绩推荐行：读 out/prebattle/info.json（按 mtime 缓存），失败给「无数据」。"""
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root, "out", "prebattle", "info.json")
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            return _T("推荐：无数据", "Recommendation: no data")
        key = (path, mtime)
        if _STRATEGY_CACHE.get("key") == key:
            return _STRATEGY_CACHE.get("line") or _T("推荐：无数据", "Recommendation: no data")
        with open(path, "r", encoding="utf-8") as f:
            info = json.load(f)
        line = _fmt_strategy_info(info)
        _STRATEGY_CACHE["key"] = key
        _STRATEGY_CACHE["line"] = line
        return line
    except Exception:
        return _T("推荐：无数据", "Recommendation: no data")




_BUILDINGS_CACHE = {"key": None, "line": ""}


def _fmt_buildings_counts(counts):
    """把分类计数压成一行文案（纯函数，便于测试）。"""
    if not counts or not counts.get("total"):
        return _T("建筑：无数据", "Buildings: no data")
    parts = []
    for key, label in (("defense", "防御"), ("economy", "经济"), ("army", "兵营"),
                       ("trap", "陷阱"), ("storage", "仓库"), ("other", "其它")):
        n = int(counts.get(key) or 0)
        if n:
            parts.append("%s %d" % (label, n))
    line = "建筑：" + " · ".join(parts)
    if counts.get("walls"):
        line += " · 墙 %d" % int(counts["walls"])
    if counts.get("maxed_pct") is not None:
        line += " · 满级 %d%%" % int(counts["maxed_pct"])
    return line


def _count_buildings(layout):
    """按分类统计当前布局（防御/经济/兵营/陷阱/仓库/其它/墙/满级占比）。"""
    out = {"total": 0, "defense": 0, "economy": 0, "army": 0, "trap": 0,
           "storage": 0, "other": 0, "walls": 0, "maxed_pct": None}
    if not isinstance(layout, dict):
        return out
    try:
        import re as _re
        from .. import levels as _levels
        from ..topdown import _category
    except Exception:
        return out
    bs = layout.get("buildings") or []
    out["walls"] = len(layout.get("walls") or [])
    m = _re.search(r"th(\d{1,2})", str(layout.get("name") or ""), _re.I)
    th = int(m.group(1)) if m else 16
    maxed = 0
    for b in bs:
        t = str(b.get("type") or "")
        cat = _category(t)
        out[cat if cat in out else "other"] += 1
        out["total"] += 1
        lv = b.get("level")
        if lv:
            try:
                if int(lv) >= int(_levels.max_level_of(t, th, strict=True) or 0):
                    maxed += 1
            except Exception:
                pass
    if out["total"]:
        out["maxed_pct"] = round(100.0 * maxed / out["total"])
    return out


_OPP_CACHE = {"key": None, "line": ""}


def _fmt_ocr_payload(payload):
    """把 out/ocr_latest.json 压成一行（纯函数，便于测试）。"""
    if not isinstance(payload, dict) or not payload:
        return _T("对手：未识别（F6）", "Opponent: unknown (F6)")
    line = payload.get("line")
    if line:
        return str(line)
    th = payload.get("th")
    ocr = payload.get("ocr") or {}
    if not th and not ocr.get("name"):
        return _T("对手：未识别（F6）", "Opponent: unknown (F6)")
    name = ocr.get("name") or "未知"
    return "对手：%s（TH%s）· OCR" % (name, th if th else "?")


def _opponent_line(state):
    """读 out/ocr_latest.json（按 mtime 缓存）；无文件给「F6 识别」。"""
    try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root, "out", "ocr_latest.json")
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            return _T("对手：未识别（F6）", "Opponent: unknown (F6)")
        key = (path, mtime)
        if _OPP_CACHE.get("key") == key:
            return _OPP_CACHE.get("line") or _T("对手：未识别（F6）", "Opponent: unknown (F6)")
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        line = _fmt_ocr_payload(payload)
        _OPP_CACHE["key"] = key
        _OPP_CACHE["line"] = line
        return line
    except Exception:
        return _T("对手：未识别（F6）", "Opponent: unknown (F6)")


def _buildings_line(state):
    """研究页建筑构成行（按 layout 指纹缓存，热路径不重算）。"""
    try:
        layout = getattr(state, "layout", None)
        if not isinstance(layout, dict):
            layout = getattr(state, "Layout", None)
        if not isinstance(layout, dict):
            return _T("建筑：无数据", "Buildings: no data")
        key = (layout.get("name"), len(layout.get("buildings") or []), len(layout.get("walls") or []))
        if _BUILDINGS_CACHE.get("key") == key:
            return _BUILDINGS_CACHE.get("line") or _T("建筑：无数据", "Buildings: no data")
        line = _fmt_buildings_counts(_count_buildings(layout))
        _BUILDINGS_CACHE.update({"key": key, "line": line})
        return line
    except Exception:
        return _T("建筑：无数据", "Buildings: no data")

def _sim_line(state):
    """P3c-3：2D 推演一行（sim_panel 指纹缓存，热路径不重算）；
    无布局 / 无候选 / 异常统一「推演：无数据」，绝不影响研究页其它行。"""
    try:
        from . import sim_panel as _sp
        return _sp.line_from_summary(
            _sp.summary_from_layout(getattr(state, "Layout", None)))
    except Exception:
        return _T("推演：无数据", "Simulation: no data")


def _bottom_status(px, H, m, ready, page, avail_w, extra=None, extra_lines=None):
    items = m.candidates if m is not None else []
    total = len(items)
    visible = sum(1 for c in items if not c.get("hidden")
                  and c["confidence"] >= _SESSION["threshold"])
    label = {PAGE_RESEARCH: _L(ready, "研究", "Research"),
             PAGE_LAYOUT: _L(ready, "阵型", "Layout"),
             PAGE_COLLECT: _L(ready, "采集", "Capture"),
             PAGE_SETTING: _L(ready, "设置", "Settings")}.get(page, page)
    # P3b-3：布局弱点明细画在状态栏上方（最多 2 行，不参与流式布局）
    _lines = [str(x) for x in (extra_lines or []) if str(x).strip()][:2]
    for _i, _ln in enumerate(_lines):
        imgui.set_cursor_screen_pos(
            imgui.ImVec2(px + PAD, H - 26.0 - 18.0 * (len(_lines) - _i)))
        imgui.text_colored(imgui.ImVec4(*GREY), _ln[:60])
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, H - 26.0))
    right = extra if extra else _L(ready, f"候选 {total} / 可见 {visible}", f"candidates {total} / visible {visible}")
    imgui.text_colored(imgui.ImVec4(*GREY), f"{label}  ·  {right}")


# ================================================================ 采集页

def _draw_collect(ctx, state, root, ready, panel_w, px, H):
    avail_w = panel_w - 2 * PAD
    farm = getattr(state, "farm", {}) or {}
    live = bool(getattr(state, "live", False))
    stats = farm.get("stats") or {}

    y = _content_top(root)
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready,
                  f"模式={farm.get('mode') or '-'}  实时={'开' if live else '演练'}",
                  f"Mode={farm.get('mode') or '-'}  Live={'on' if live else 'dry'}"))
    y += 22.0
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(f"已侦察 {stats.get('scouted', 0)} 跳过 {stats.get('skipped', 0)} "
               f"错误 {stats.get('errors', 0)} 开菜单 {stats.get('menu_opened', 0)}")
    y += 22.0
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text_colored(imgui.ImVec4(*GREY), f"报告时间 {farm.get('timestamp') or '—'}")
    for b in farm.get("blockers") or []:
        y += 18.0
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
        imgui.text_colored(imgui.ImVec4(*RED), "• " + str(b)[:96])
    y += GAP + BTN_H + GAP

    # 操作行：开始 / 停止 / Live 切换（按钮 28px，8px 间距；统一三态）
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "开始采集", "Start capture"),
            imgui.ImVec2(110.0, BTN_H), kind="pri", key="collect_start"):
        ctx.request_farm_start()
        ctx.log("collect: request start")
    imgui.same_line(spacing=GAP)
    if _btn(_L(ready, "停止", "Stop capture"),
            imgui.ImVec2(90.0, BTN_H), kind="sec", key="collect_stop"):
        ctx.request_farm_stop()
        ctx.log("collect: request stop")
    imgui.same_line(spacing=GAP)
    if _btn(("开启实时" if not live else "关闭实时"),
            imgui.ImVec2(90.0, BTN_H),
            kind="pri" if live else "sec", key="collect_live"):
        ctx.set_live(not live)
        ctx.log(f"collect: live -> {not live}")
    y += BTN_H + GAP

    # clicks.log 尾部 20 行（高度随内容收缩，封顶 160px，不拉满；C6）
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, "最近点击日志（末 20 行）", "Recent clicks (last 20)"))
    y += 22.0
    lines, err = data.read_clicks_tail(os.path.join(root, "out", "overlay", "clicks.log"), n=20)
    # P1-4：日志框按可用高度伸缩（720 不留空白），短高由 avail 自然收小
    child_h = max(80.0, min(320.0, (H - 44.0) - y))
    imgui.begin_child("clicks", imgui.ImVec2(avail_w, child_h),
                      imgui.ChildFlags_.borders)
    if err:
        imgui.text_colored(imgui.ImVec4(*GREY), f"({err})")
    for ln in reversed(lines):
        imgui.text_colored(imgui.ImVec4(*GREY), str(ln)[:110])
    imgui.end_child()

    _bottom_status(px, H, _SESSION["model"], ready, PAGE_COLLECT, avail_w)


# ================================================================ 设置页

def _keys_ensure_loaded(root):
    """设置页进入时载入绑键表；读失败由 keys 回退默认并把 warn 放到消息行。"""
    if _SESSION.get("keys_loaded_root") == root:
        return
    keybind.load(root)
    _SESSION["keys_loaded_root"] = root
    warns = keybind.pop_warns()
    if warns:
        _SESSION["keys_msg"] = ("neutral", "；".join(warns))


def _keys_capture_poll(ctx):
    """捕获态轮询下一个按键（GetAsyncKeyState 全局，不要求窗口焦点）。

    ESC=取消（不绑定）；命中后 keybind.set_key 落盘并回写 _SESSION["keys_msg"]。
    """
    cap = _SESSION.get("keys_capture")
    if not cap:
        return
    user32 = ctypes.windll.user32
    prev = _SESSION.setdefault("keys_prev_vk", {})
    for vk in keybind.WATCH_VKS:
        now = bool(user32.GetAsyncKeyState(vk) & 0x8000)
        was = prev.get(vk, False)
        if now and not was:
            prev[vk] = now
            if vk == 0x1B:  # ESC = 取消，不当绑定值
                _SESSION["keys_capture"] = None
                _SESSION["keys_msg"] = ("neutral", "已取消")
                return
            key = keybind.key_from_vk(vk)
            if key:
                ok, kind, msg = keybind.set_key(cap, key)
                _SESSION["keys_msg"] = (kind, msg)
                _SESSION["keys_capture"] = None
                ctx.log(f"keys: {cap} -> {key} ({msg})")
            return
        prev[vk] = now


def _draw_setting(ctx, state, root, ready, panel_w, px, H):
    avail_w = panel_w - 2 * PAD
    paths = data.Paths(root)
    # 顶部固定栈（标签/状态/引擎按钮+说明）约占到 content_top+34，
    # 设置页从这里再往下排，避免锚点行压住引擎说明（实机重叠问题）。
    y = _content_top(root) + 34.0


    # ---- 竖向预算（C7）：563 实机高度下全部行在框内，ESC 说明行 [清除] 括号可见。
    # 预算：锚点段 74 + 快捷键段(22 + 5×26=152) + 消息行18 + 恢复/ESC 行26
    #       + 偏移段(18+24) = ~312，留 ~90px 安全垫到状态栏(537)。

    # ---- 锚点表（标题行 + 前 3 条紧凑内联，不建固定高度子框，省纵向空间） ----
    anchors = data.load_anchors(paths)["anchors"]
    # 审计 R2/R3：旧 _c6_gap 按低估的 _fixed 把余量均摊成 4×18px，
    # 563 实机高时把底部段下推出框、撞钉死的退出行；已删除该均摊，
    # 全部内容自然流、段间固定 4px，退出行紧随其后，不再硬钉 H-56。
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, f"实测锚点 {len(anchors)} 条（灰=未验证）",
                   f"Anchors {len(anchors)} (grey=unverified)"))
    y += 18.0
    # 审计 R3 压缩：前 3 条并入一行折行（text_wrapped 到面板宽），不再各占一行；
    # 不缩字号，只合并行距，省 ~32px 纵向预算。
    # 调试锚点默认隐藏（技术数据，普通用户不需要）；config/overlay.json 里
    # "show_anchor_debug": true 才显示完整锚点坐标。
    _show_dbg = False
    try:
        _ov, _err = data.load_json(os.path.join(root, "config", "overlay.json"))
        _show_dbg = bool((_ov or {}).get("show_anchor_debug", False))
    except Exception:
        _show_dbg = False
    if _show_dbg:
        _anchor_brief = "  ".join(
            (f"{a['key']}({a['point'][0]},{a['point'][1]})"
             if a["confirmed"] else f"{a['key']}({a['point'][0]},{a['point'][1]})·未验证")
            for a in anchors[:3]) or "—"
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
        imgui.text_wrapped(_anchor_brief)
        y += 34.0
        if len(anchors) > 3:
            imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
            imgui.text_colored(imgui.ImVec4(*DIM),
                               f"…其余 {len(anchors) - 3} 条见 config/anchors.json")
            y += 16.0
    y += 4.0

    # ---- 快捷键绑定表（可改键 / 可清除 / 可恢复默认；行高 22，三态按钮） ----
    _keys_ensure_loaded(root)
    _keys_capture_poll(ctx)
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, _T("快捷键绑定", "Hotkeys"), "Hotkeys"))
    # P1-5：默认键已避开雷电热键（F8/F9/F11）；占用键只在行内黄警，不加后缀
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + 96.0, y))
    imgui.text_colored(imgui.ImVec4(*GREY),
                       _L(ready, _T("默认键已避开雷电热键（F8/F9/F11）", "Default keys avoid LDPlayer hotkeys (F8/F9/F11)"),
                          "Defaults avoid LDPlayer hotkeys (F8/F9/F11)"))
    y += 20.0
    bindings = keybind.bindings()
    row_h = 22.0
    row_gap = 0.0  # 审计 R3 压缩：行内 4px 间隙去掉，5 行省 20px（不缩字号）
    for i, d in enumerate(keybind.ACTION_DEFS):
        row_y = y + i * (row_h + row_gap)
        aid = d["id"]
        cur = bindings.get(aid) or ""
        cap_active = _SESSION.get("keys_capture") == aid
        # 左：中文名（捕获态替换为提示，避免与键列按钮列重叠）
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, row_y + 4.0))
        if cap_active:
            imgui.text_colored(imgui.ImVec4(*theme.WARN), "按新键（ESC）")
        else:
            imgui.text(_L(ready, d["zh"], d.get("en") or d["zh"]))
        # 中：当前键（未绑定显示「未绑定」）；键列右对齐，终点让开按钮列。
        # P1-5：仅 f8/f9/f11（雷电占用）显黄色警告；Insert/Delete/F7/F12/ESC 等正常键
        # 不显示任何后缀。
        if not cap_active:
            label = keybind.display(cur) if cur else "未绑定"
            res = keybind.RESERVED_LD.get((cur or "").lower())
            lw = imgui.calc_text_size(label).x
            key_x = px + panel_w - PAD - 160.0 - lw
            imgui.set_cursor_screen_pos(imgui.ImVec2(key_x, row_y + 4.0))
            if res:
                imgui.text_colored(imgui.ImVec4(*YELLOW),
                                   f"{label}（雷电占用·{res}）")
            else:
                imgui.text_colored(imgui.ImVec4(*INK), label)
        # 右：[改键]/[取消]（最右） [清除]（其左）；三态灰按钮
        bx = px + panel_w - PAD - 62.0
        imgui.set_cursor_screen_pos(imgui.ImVec2(bx, row_y))
        if _btn((_L(ready, "取消", "Cancel") if cap_active else _L(ready, "改键", "Rebind")) + f"##{aid}",
                imgui.ImVec2(62.0, row_h), kind="sec", key=f"key_{aid}"):
            if cap_active:
                _SESSION["keys_capture"] = None
                _SESSION["keys_msg"] = ("neutral", "已取消")
            else:
                _SESSION["keys_capture"] = aid
                _SESSION["keys_msg"] = None
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + panel_w - PAD - 62.0 - 8.0 - 52.0, row_y))
        if _btn(f"{_L(ready, '清除', 'Clear')}##{aid}", imgui.ImVec2(52.0, row_h),
                kind="sec", key=f"clear_{aid}"):
            ok, kind, msg = keybind.clear_key(aid)
            _SESSION["keys_msg"] = (kind, msg)
            ctx.log(f"keys: clear {aid}")
    y += len(keybind.ACTION_DEFS) * (row_h + row_gap)

    # ---- 消息行（红=冲突拒绝 / 黄=雷电占用警示 / 绿=已保存 / 灰=中性） ----
    msg = _SESSION.get("keys_msg")
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y + 2.0))
    if msg:
        kind, text = msg
        col = RED if kind == "red" else (YELLOW if kind == "yellow"
                                          else (GREEN if kind == "green" else GREY))
        imgui.text_colored(imgui.ImVec4(*col), text)
    else:
        imgui.text_colored(imgui.ImVec4(*GREY), _T("已保存 overlay_keys.json", "Saved overlay_keys.json"))
    y += 20.0  # 审计 R5：文字底到下一行按钮顶留足 4px，不再微触

    # ---- 恢复默认（左）；ESC 提示同行右对齐，[清除] 右括号必在框内（C7）----
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, "恢复默认", "Reset to defaults"), imgui.ImVec2(110.0, 24.0),
            kind="sec", key="keys_reset"):
        ok, kind, msg = keybind.reset()
        _SESSION["keys_msg"] = (kind, msg)
        ctx.log("keys: reset to defaults")
    _text_right(_L(ready, "ESC 取消捕获；解绑用 [清除]",
                   "ESC cancels capture; use Clear to unbind"),
                GREY, px, panel_w, y + 5.0)
    y += 26.0

    # ---- 面板位置：右 / 下 / 内（外置窗口；落盘 config/overlay.json，默认右） ----
    y += 4.0
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, _T("面板位置（外置窗口）", "Panel position (external window)"), "Panel position"))
    y += 18.0
    try:
        from . import config as _ovcfg
        _pos_cfg = _ovcfg.load_overlay_config(root)
        cur_pos = str(_pos_cfg.get("panel_position", "right")).lower()
    except Exception:
        _pos_cfg, cur_pos = None, "right"
    for i, (label, key) in enumerate((("右", "right"), ("下", "down"), ("内", "inner"))):
        bx = px + PAD + i * 78.0
        imgui.set_cursor_screen_pos(imgui.ImVec2(bx, y))
        kind = "amber" if cur_pos == key else "sec"
        if _btn(_L(ready, label, key), imgui.ImVec2(70.0, 22.0),
                kind=kind, key=f"panelpos_{key}"):
            if _pos_cfg is not None:
                _pos_cfg["panel_position"] = key
                _ovcfg.save_overlay_config(root, _pos_cfg)
            rt = getattr(ctx, "rt", None)
            if rt is not None and getattr(rt, "cfg", None) is not None:
                rt.cfg["panel_position"] = key
            cur_pos = key
            ctx.log(f"panel_position={key} saved")
    y += 24.0

    # ---- P1-6 一键重对位：接 vision.detect_boundary/safe_calib（不改其内部）；禁 F11 ----
    y += 4.0
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, _T("重新对位", "Recalibrate"), "Recalibrate"), imgui.ImVec2(150.0, 24.0),
            kind="sec", key="recalib_btn"):
        ctx.request_recalib()
    rk = ctx.recalib_msg if hasattr(ctx, "recalib_msg") else ("neutral", "")
    if rk and rk[1]:
        rcol = GREEN if rk[0] == "green" else (YELLOW if rk[0] == "yellow" else GREY)
        imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD + 162.0, y + 5.0))
        imgui.text_colored(imgui.ImVec4(*rcol), rk[1])
    y += 26.0
    # HUD「视角可能已变」角标开关（低干扰、可关）
    y += 4.0
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    vw = ctx.view_warn if hasattr(ctx, "view_warn") else False
    _, vw_new = imgui.checkbox(_L(ready, _T("HUD 显示「视角可能已变」角标", "Show 'view may have changed' badge on HUD"),
                                 "Show the view-may-have-changed badge on HUD"), vw)
    if vw_new != vw:
        ctx.set_view_warn(vw_new)
    y += 22.0

    # ---- 贴合偏移 dx/dy（标签一行，dx/dy 同排第二行，不压右缘） ----
    y += 4.0
    off = _load_offset(root)
    if _SESSION["offset_dx"] is None:
        _SESSION["offset_dx"] = ctypes.c_float(float(off.get("dx", 0) or 0))
        _SESSION["offset_dy"] = ctypes.c_float(float(off.get("dy", 0) or 0))
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    imgui.text(_L(ready, _T("贴合偏移（保存由运行时写 config）", "Fit offset (runtime saves to config)"),
                  "Fit offset (saved by the runtime)"))
    y += 18.0
    # 输入框去 ImGui 默认蓝：frame/步进按钮统一灰系（C1）
    sec = theme.secondary_states()
    imgui.push_style_color(imgui.Col_.frame_bg, theme.SEC_BG)
    imgui.push_style_color(imgui.Col_.button, sec["normal"])
    imgui.push_style_color(imgui.Col_.button_hovered, sec["hover"])
    imgui.push_style_color(imgui.Col_.button_active, sec["pressed"])
    imgui.push_style_color(imgui.Col_.text, INK)
    imgui.push_item_width(110.0)
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y + 2.0))
    chg_dx, v_dx = imgui.input_float("dx", float(_SESSION["offset_dx"].value),
                                     1.0, 5.0, "%.0f")
    if chg_dx:
        _SESSION["offset_dx"].value = v_dx
    imgui.same_line(spacing=20.0)
    chg_dy, v_dy = imgui.input_float("dy", float(_SESSION["offset_dy"].value),
                                     1.0, 5.0, "%.0f")
    if chg_dy:
        _SESSION["offset_dy"].value = v_dy
    imgui.pop_item_width()
    for _ in range(5):
        imgui.pop_style_color()
    y += 22.0

    # ---- P0-2 第二条退出路径：面板「退出覆盖层」按钮（WM_CLOSE 由 glfw 回调接住） ----
    # 审计 R2/R4：不再硬钉 H-56（与流式 checkbox/偏移行相撞、英文提示出右缘）；
    # 自然流紧随偏移段，段间 4px，提示右对齐并夹在面板内边距内，按钮底留状态栏。
    y += 4.0
    imgui.set_cursor_screen_pos(imgui.ImVec2(px + PAD, y))
    if _btn(_L(ready, _T("退出覆盖层", "Exit overlay"), "Exit"), imgui.ImVec2(150.0, 24.0),
            kind="sec", key="panel_exit"):
        ctx.request_exit()
    y += 28.0
    # 退出提示只在剩余空间放得下时绘制（底界 H-44），贴底则省略，不骑线横切
    _exit_hint = _L(ready, "（窗口关闭按钮 / 任务管理器亦可退出）",
                    "(closing the window also exits)")
    if y + 18.0 <= H - 44.0:
        _hw = imgui.calc_text_size(_exit_hint).x
        _hx = px + panel_w - PAD - _hw
        if _hx > px + PAD + 162.0:
            imgui.set_cursor_screen_pos(imgui.ImVec2(_hx, y))
            imgui.text_colored(imgui.ImVec4(*GREY), _exit_hint)

    _bottom_status(px, H, _SESSION["model"], ready, PAGE_SETTING, avail_w)


def _load_hotkeys(root):
    """合并 overlay.config 默认热键与 config/overlay.json 覆盖（只读）。"""
    out = {}
    try:
        from . import config as ovcfg
        merged = ovcfg.load_overlay_config(root)
        hk = merged.get("hotkeys") or {}
        if isinstance(hk, dict):
            out.update(hk)
    except Exception:
        raw, err = data.load_json(os.path.join(root, "config", "overlay.json"))
        if err is None and isinstance(raw, dict):
            out.update(raw.get("hotkeys") or {})
    return out


def _load_offset(root):
    try:
        from . import config as ovcfg
        merged = ovcfg.load_overlay_config(root)
        return merged.get("offset") or {}
    except Exception:
        raw, _ = data.load_json(os.path.join(root, "config", "overlay.json"))
        return (raw or {}).get("offset") or {}
