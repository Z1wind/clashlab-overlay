# -*- coding: utf-8 -*-
"""战术知识库（clashlab.knowledge）。

职责：
1. load_cards(dir)        读取 knowledge/tactics/*.json 战术卡；
2. retrieve(profile, brief, k=3)  轻量关键词/BM25 式打分检索，返回 [(card, reason)]；
3. build_index(out)       生成人工可查的 knowledge/index.json。

设计原则（与项目诚实性要求一致）：
- 只检索落盘卡片，绝不编造；无命中返回空列表并记 no_knowledge；
- 打分只看卡片上写出来的字段（th/army/equipment/pattern/countered_layout + 标题/要点词面）；
- 本模块不调用大模型、不联网，可独立运行：
  python -m clashlab.knowledge build|ls|retrieve --th 13 --army edrag --equipment giant-arrow
"""
import argparse
import json
import logging
import os
import re
import sys

LOG = logging.getLogger("clashlab.knowledge")

# 与 schema 约定保持一致的词表（未知值不报错，只是不参与加权）
PATTERNS = {"queen_charge", "edrag_rush", "hybrid", "blimp"}
LAYOUTS = {"ring", "box", "island", "anti-3star"}

# 本库用到的 equipment id（小写连字符；config/heroes.json 由另一智能体维护，
# 若命名冲突以 heroes.json 为准，这里只做库内自洽）：
#   giant-arrow 巨型箭 / invisibility-vial 隐形药水 / action-figure 动作人偶 /
#   frozen-arrow 冰箭 / eternal-tome 永恒书卷 / rage-gem 狂暴宝石 / fireball 大火球 /
#   electro-boots 雷霆战靴 / rocket-spear 火箭飞矛 / giant-gauntlet 巨化手套 /
#   spiky-ball 尖刺足球 / hog-puppet 野猪木偶 / haste-vial 急速药水 /
#   healing-tome 治疗书卷 / magic-mirror 克隆魔镜
# army id：edrag 雷龙 / dragon 龙 / balloon 气球 / lava-hound 熔岩猎犬 /
#   hog-rider 野猪骑士 / miner 矿工 / super-witch 超巫 / witch 女巫 /
#   ice-golem 冰戈仑 / super-wizard 超法 / root-rider 根骑士 /
#   dragon-rider 龙骑士 / yeti 雪怪 / bat 蝙蝠法术 / healer 治疗天使

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_TACTICS_DIR = os.path.join(ROOT, "knowledge", "tactics")
DEFAULT_INDEX = os.path.join(ROOT, "knowledge", "index.json")


# ---------------------------------------------------------------- 工具
def _norm(v):
    return str(v or "").strip().lower()


def _split_list(v):
    """把 'a,b' / ['a','b'] 统一成小写字符串列表。"""
    if v is None:
        return []
    if isinstance(v, str):
        parts = re.split(r"[,，;/\s]+", v)
    else:
        parts = list(v)
    return [p.strip().lower() for p in parts if str(p).strip()]


def _th_digits(v):
    m = re.search(r"(\d+)", str(v or ""))
    return m.group(1) if m else ""


def _resolve_dir(dir_arg):
    if not dir_arg:
        return DEFAULT_TACTICS_DIR
    if os.path.isabs(dir_arg):
        return dir_arg
    return os.path.join(os.getcwd(), dir_arg)


# ---------------------------------------------------------------- 加载
# 结果级缓存：同一目录只在 mtime 变化时重读 44 张卡；retrieve 每次调用不再全量开文件。
_CARD_CACHE: dict = {}


def _dir_mtime(d):
    """目录内全部 .json 的最大 mtime；目录缺失返回 None。"""
    try:
        return max(os.path.getmtime(os.path.join(d, fn))
                   for fn in os.listdir(d) if fn.endswith(".json"))
    except (OSError, ValueError):
        return None


def load_cards(dir="knowledge/tactics"):
    """读取目录下全部战术卡 JSON，返回卡片列表；目录不存在或为空返回 []。

    mtime 未变直接返回缓存（避免每次 retrieve 重读 44 张卡）；任一卡更新即失效重读。
    """
    d = _resolve_dir(dir)
    if not os.path.isdir(d):
        LOG.warning("no_knowledge: 战术卡目录不存在 %s", d)
        return []
    mt = _dir_mtime(d)
    hit = _CARD_CACHE.get(d)
    if hit is not None and hit[0] == mt:
        return hit[1]

    cards = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(d, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                card = json.load(f)
        except Exception as e:  # 单张坏卡不拖垮整库
            LOG.warning("跳过坏卡 %s: %s", fn, e)
            continue
        if not isinstance(card, dict) or not card.get("id"):
            continue
        card.setdefault("_file", fn)
        cards.append(card)
    _CARD_CACHE[d] = (mt, cards)
    return cards


# ---------------------------------------------------------------- 打分
def _token_bag(card):
    """标题/要点的词面兜底：拉丁词 + 中文二元组，用于字段全不命中时的弱匹配。"""
    text = " ".join([
        _norm(card.get("source", {}).get("title", "")),
        " ".join(card.get("key_points", []) or []),
        _norm(card.get("pattern", "")),
    ])
    tokens = set(re.findall(r"[a-z0-9]+", text))
    # 中文二元组
    han = re.findall(r"[一-鿿]", text)
    for i in range(len(han) - 1):
        tokens.add(han[i] + han[i + 1])
    return tokens


def score_card(card, brief):
    """返回 (score, reasons)。brief: {th, army, equipment, pattern, countered_layout}，均可选。"""
    score = 0.0
    reasons = []

    # th 命中（卡面 th 为空则不参与本项）
    card_th = _th_digits(card.get("th"))
    q_th = _th_digits(brief.get("th"))
    if card_th and q_th and card_th == q_th:
        score += 3.0
        reasons.append(f"th 命中 {q_th}")

    # army 重叠
    card_army = set(_split_list(card.get("army")))
    q_army = set(_split_list(brief.get("army")))
    hit_army = card_army & q_army
    if hit_army:
        score += 2.0 * len(hit_army)
        reasons.append("army 命中 " + "/".join(sorted(hit_army)))

    # equipment 重叠（高权重：装备是本库主索引维度之一）
    card_eq = set(_split_list(card.get("equipment")))
    q_eq = set(_split_list(brief.get("equipment")))
    hit_eq = card_eq & q_eq
    if hit_eq:
        score += 3.0 * len(hit_eq)
        reasons.append("equipment 命中 " + "/".join(sorted(hit_eq)))

    # pattern 精确
    card_pat = _norm(card.get("pattern"))
    q_pat = _norm(brief.get("pattern"))
    if card_pat and q_pat and card_pat == q_pat:
        score += 3.0
        reasons.append(f"pattern 命中 {q_pat}")

    # countered_layout 精确
    card_layout = _norm(card.get("countered_layout"))
    q_layout = _norm(brief.get("countered_layout"))
    if card_layout and q_layout and card_layout == q_layout:
        score += 2.0
        reasons.append(f"layout 命中 {q_layout}")

    # 词面兜底：brief 里给的自由词在标题/要点里出现
    q_tokens = set(_split_list(brief.get("keywords")))
    if q_tokens:
        bag = _token_bag(card)
        hit_kw = {t for t in q_tokens if t in bag}
        if hit_kw:
            score += 0.5 * len(hit_kw)
            reasons.append("关键词命中 " + "/".join(sorted(hit_kw)))

    return score, reasons


def retrieve(profile=None, brief=None, k=3, dir="knowledge/tactics"):
    """检索战术卡。

    参数：
      profile: 可选 dict（与 brief 合并，兼容上层把 profile 当查询用）；
      brief:   {th, army, equipment, pattern, countered_layout, keywords}；
      k:       返回前 k 条。
    返回 [(card, reason_list)]；无命中返回 []，并记一条 no_knowledge 日志。
    """
    brief = dict(brief or {})
    if isinstance(profile, dict):
        for key in ("th", "army", "equipment", "pattern", "countered_layout", "keywords"):
            if profile.get(key) and not brief.get(key):
                brief[key] = profile[key]

    cards = load_cards(dir)
    if not cards:
        LOG.warning("no_knowledge: 战术库为空（%s）", dir)
        return []

    ranked = []
    for card in cards:
        s, reasons = score_card(card, brief)
        if s > 0:
            ranked.append((s, card, reasons))
    ranked.sort(key=lambda x: -x[0])

    if not ranked:
        LOG.warning("no_knowledge: 无卡片命中 brief=%s", json.dumps(brief, ensure_ascii=False))
        return []

    out = []
    for s, card, reasons in ranked[:k]:
        reason = reasons + [f"score={s:.1f}"]
        out.append((card, reason))
    return out


# ---------------------------------------------------------------- 索引
def build_index(out="knowledge/index.json", dir="knowledge/tactics"):
    """生成人工可查索引：id/title/site/pattern/th/equipment/confidence/url/一句话摘要。"""
    cards = load_cards(dir)
    rows = []
    for c in cards:
        src = c.get("source", {}) or {}
        kp = c.get("key_points", []) or []
        summary = kp[0] if kp else _norm(src.get("title"))
        rows.append({
            "id": c.get("id"),
            "title": src.get("title", ""),
            "site": src.get("site", ""),
            "pattern": c.get("pattern", ""),
            "th": str(c.get("th", "")),
            "equipment": c.get("equipment", []),
            "confidence": c.get("confidence"),
            "url": src.get("url", ""),
            "summary": summary[:80],
        })
    rows.sort(key=lambda r: str(r["id"]))
    out_path = out if os.path.isabs(out) else os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return rows, out_path


# ---------------------------------------------------------------- CLI
def _cmd_build(args):
    rows, path = build_index(out=args.out, dir=args.dir)
    print(f"[build] {len(rows)} 张卡 -> {path}")


def _cmd_ls(args):
    cards = load_cards(args.dir)
    print(f"共 {len(cards)} 张卡：")
    for c in cards:
        src = c.get("source", {}) or {}
        print(f"  {c.get('id')} | {src.get('site')} | th{c.get('th')} | "
              f"{c.get('pattern')} | conf={c.get('confidence')} | {src.get('title', '')[:40]}")


def _cmd_retrieve(args):
    brief = {
        "th": args.th, "army": args.army, "equipment": args.equipment,
        "pattern": args.pattern, "countered_layout": args.layout,
        "keywords": args.keywords,
    }
    hits = retrieve(brief=brief, k=args.k, dir=args.dir)
    if not hits:
        print("[retrieve] no_knowledge：无卡片命中，返回空列表（不编造）")
        return
    for i, (card, reasons) in enumerate(hits, 1):
        src = card.get("source", {}) or {}
        print(f"#{i} {card['id']} | {src.get('site')} | th{card.get('th')} | "
              f"{card.get('pattern')} | conf={card.get('confidence')}")
        print(f"    标题: {src.get('title', '')[:60]}")
        print(f"    命中理由: {'; '.join(reasons)}")
        print(f"    URL: {src.get('url', '')}")


def main(argv=None):
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="clashlab.knowledge", description="战术知识库 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dir", default="knowledge/tactics", help="战术卡目录")

    p_build = sub.add_parser("build", parents=[common], help="生成 index.json")
    p_build.add_argument("--out", default="knowledge/index.json")
    p_build.set_defaults(func=_cmd_build)

    p_ls = sub.add_parser("ls", parents=[common], help="列出全部卡片")
    p_ls.set_defaults(func=_cmd_ls)

    p_get = sub.add_parser("retrieve", parents=[common], help="检索")
    p_get.add_argument("--th", default="")
    p_get.add_argument("--army", default="")
    p_get.add_argument("--equipment", default="")
    p_get.add_argument("--pattern", default="")
    p_get.add_argument("--layout", default="")
    p_get.add_argument("--keywords", default="")
    p_get.add_argument("--k", type=int, default=3)
    p_get.set_defaults(func=_cmd_retrieve)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
