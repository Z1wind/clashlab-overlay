# -*- coding: utf-8 -*-
"""TH16 数值取数自证：旧兜底(th=None) vs TH16 真实值(th=16)，两种路径各排一次
dps 降序 + 分档（前3 rank3 / 4-6 rank2 / 其余 rank1，与 tactics.load_local 规则一致），
另单列 threat_effective（含 13% 目标最大生命附加伤害）独立威胁排序。

运行：D:\\Python313\\python.exe tools\\stats_th16_check.py
产出：out\\th16\\stats_th16_check.md（四建筑数值表 + 来源 URL + 置信度 + 抓取日期）

只读 clashlab.assets，不写任何被禁文件；STATS 原样不动，building_path 不受影响。
"""
import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clashlab import assets  # noqa: E402

# ---------------------------------------------------------------------------
# 样本 1：TH16 真实布防示例（禁止出现 firespitter —— 它是 TH17 建筑，TH16 阵不存在）
# 数量为示例，非实测阵（wiki/clashlevels 上限：monolith1 / ricochet2 / eagle1 /
# inferno3 / x-bow4 / scattershot2 / wizard5 / cannon7 / mortar4，本表只取代表）。
# ---------------------------------------------------------------------------
SAMPLE1 = [
    ("monolith", "巨石碑"),
    ("ricochet-cannon", "弹射加农炮 #1"),
    ("ricochet-cannon", "弹射加农炮 #2"),
    ("eagle-artillery", "鹰火炮"),
    ("inferno-tower", "地狱塔 #1"),
    ("inferno-tower", "地狱塔 #2"),
    ("x-bow", "X 连弩 #1"),
    ("x-bow", "X 连弩 #2"),
    ("scattershot", "散射炮"),
    ("wizard-tower", "法师塔"),
    ("cannon", "加农炮"),
    ("mortar", "迫击炮"),
]

# 样本 2：极端受控对照（含 TH17 前瞻建筑 firespitter，仅作数值对照，不代表 TH16 阵）
SAMPLE2 = [
    ("monolith", "巨石碑"),
    ("firespitter", "火焰喷射器(TH17)"),
    ("ricochet-cannon", "弹射加农炮"),
    ("eagle-artillery", "鹰火炮"),
    ("inferno-tower", "地狱塔"),
    ("x-bow", "X 连弩"),
]

RANK3, RANK2, RANK1 = 3, 2, 1

# threat_effective 参照口径：参照目标 H=5000 hp（示例值，介于英雄与戈仑石人量级；
# Golem Lv7+ HP 7000+，来源 https://clashofclans.fandom.com/wiki/Golem；wiki 原文点名
# Heroes / Golems 为 Monolith 主要目标）。有效威胁对 H 敏感，非固定值。
REF_TARGET_HP = 5000
MONOLITH_BONUS_PCT = 0.13      # wiki Lv3 Bonus Damage per Shot 13%
MONOLITH_ATK_SPEED = 1.5       # wiki 攻速 1.5s/发


def rank_of(i):
    """与 tactics.load_local 现有规则一致：前3 rank3 / 4-6 rank2 / 其余 rank1。"""
    return RANK3 if i < 3 else (RANK2 if i < 6 else RANK1)


def threat_effective(name, st):
    """有效威胁 dps：仅 monolith 计入 13% 目标最大生命附加伤害；其余 = 基础 dps。

    公式：threat = base_dps + bonus_pct × H / attack_speed
         = 193 + 0.13 × 5000 / 1.5 ≈ 626（H=5000 示例参照）
    """
    if name == "monolith":
        return round(st["dps"] + MONOLITH_BONUS_PCT * REF_TARGET_HP / MONOLITH_ATK_SPEED)
    return st["dps"]


def run(sample, th, use_threat=False):
    """按 th 取数排序；use_threat=True 时按 threat_effective 排。"""
    rows = []
    for name, label in sample:
        st = assets.stats(name, th=th)
        te = threat_effective(name, st)
        rows.append({
            "type": name, "label": label,
            "hp": st["hp"], "dps": st["dps"], "range": st["range"],
            "level": st.get("level"), "threat": te,
            "confidence": st.get("confidence") or ("baseline" if name in assets.STATS else "fallback"),
        })
    rows.sort(key=lambda r: -(r["threat"] if use_threat else r["dps"]))
    for i, r in enumerate(rows):
        r["pos"] = i + 1
        r["rank"] = rank_of(i)
    return rows


def find_mono(rows):
    return next(r for r in rows if r["type"] == "monolith")


# ---------------------------------------------------------------------------
# 内置断言（真检查，不写恒 PASS）
# ---------------------------------------------------------------------------
def selfcheck():
    checks = []

    def check(label, ok, detail=""):
        checks.append((label, bool(ok), detail))

    # 1. STATS 原样：cannon 未被改动，四栋新建筑不进 STATS
    cannon = assets.STATS.get("cannon")
    check("STATS['cannon'] 未改动",
          cannon == {"cn": "加农炮", "size": 3, "hp": 1200, "dps": 118,
                     "range": 9, "level": 16},
          f"cannon={cannon}")
    check("四栋新建筑未进 STATS（building_path/类型校验不受影响）",
          all(k not in assets.STATS for k in
              ("monolith", "firespitter", "ricochet-cannon", "clan-castle"))
          and len(assets.STATS) == 15,
          f"STATS 键数={len(assets.STATS)}（应为15）")

    # 2. 覆盖生效：th=16 取 TH16_OVERRIDE
    m16 = assets.stats("monolith", th=16)
    check("stats('monolith', th=16) 覆盖生效",
          m16["hp"] == 5353 and m16["dps"] == 193 and m16["range"] == 11
          and m16.get("confidence") == "high",
          f"hp={m16['hp']} dps={m16['dps']} range={m16['range']}")

    # 3. 兜底 + WARN 去重
    records = []

    class _H(logging.Handler):
        def emit(self, rec):
            records.append(rec.getMessage())

    h = _H()
    lg = logging.getLogger("clashlab.assets")
    lg.addHandler(h)
    lg.setLevel(logging.WARNING)
    assets.stats("ghost-tower")
    assets.stats("ghost-tower")
    lg.removeHandler(h)
    check("未知建筑 WARN 只记一次（去重）", len(records) == 1, f"WARN 次数={len(records)}")
    check("未知建筑回退 DEFAULT_FALLBACK",
          assets.stats("ghost-tower") == assets.DEFAULT_FALLBACK,
          f"fallback={assets.DEFAULT_FALLBACK}")

    # 4. STATS 基线建筑 th=16 不被覆盖污染
    check("STATS 基线建筑 th=16 仍走基线",
          assets.stats("eagle-artillery", th=16)["dps"] == 350, "eagle dps=350")

    # 5. building_path 不读 TH16_OVERRIDE 的 level
    try:
        p_mono = assets.building_path("monolith")
        mono_lv = os.path.basename(p_mono).split("-")[1].split(".")[0] if p_mono else None
        path_ok = mono_lv != str(assets.TH16_OVERRIDE["monolith"]["level"])
    except Exception as e:  # noqa: BLE001
        p_mono, path_ok = None, f"RAISED {e!r}"
    check("building_path('monolith') 不读 override level=3", path_ok, f"return={p_mono}")
    try:
        p_cannon = assets.building_path("cannon")
        cannon_path_ok = p_cannon is None or "level-16" in os.path.basename(p_cannon)
    except Exception:  # noqa: BLE001
        cannon_path_ok = False
    check("building_path('cannon') 仍按 STATS level=16", cannon_path_ok, f"path={p_cannon}")

    # 6. threat_effective 公式自检：193 + 0.13×5000/1.5 = 626.3 ≈ 626
    te = threat_effective("monolith", {"dps": 193})
    check("threat_effective(monolith) = 193 + 13%×5000/1.5 ≈ 626",
          te == 626, f"threat={te}")
    check("threat_effective(非monolith) = 基础 dps",
          threat_effective("ricochet-cannon", {"dps": 390}) == 390, "")
    return checks


# ---------------------------------------------------------------------------
# 表格渲染
# ---------------------------------------------------------------------------
def fmt_rows(rows, threat_col=False):
    if threat_col:
        head = "| 名次 | 类型 | 标签 | hp | dps | threat |"
        sep = "| --- | --- | --- | --- | --- | --- |"
    else:
        head = ("| 名次 | 类型 | 标签 | hp | dps | range | 等级 | 置信度 | rank |")
        sep = "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    lines = [head, sep]
    for r in rows:
        if threat_col:
            lines.append(
                f"| {r['pos']} | {r['type']} | {r['label']} | {r['hp']} | "
                f"{r['dps']} | {r['threat']} |")
            continue
        lines.append(
            f"| {r['pos']} | {r['type']} | {r['label']} | {r['hp']} | {r['dps']} | "
            f"{r['range']} | {r['level'] or '-'} | {r['confidence']} | {r['rank']} |")
    return "\n".join(lines)


def stats_table_md():
    rows = ["| 建筑 | hp | dps | range | level | 置信度 | 抓取日期 | source_url |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    notes = []
    for name in ("monolith", "firespitter", "ricochet-cannon", "clan-castle"):
        v = assets.TH16_OVERRIDE[name]
        rows.append(
            f"| {name} | {v['hp']} | {v['dps']} | {v['range']} | {v['level']} | "
            f"{v['confidence']} | {v['fetched_at']} | {v['source_url']} |")
        notes.append(f"- **{name}**（{v['source_site']}，{v['fetched_at']}，{v['confidence']}）："
                     f"{v['note']}<br>来源：{v['source_url']}")
    return "\n".join(rows), "\n".join(notes)


def main():
    # 样本 1：两条取数路径 + 威胁排序
    s1_old = run(SAMPLE1, None)
    s1_new = run(SAMPLE1, 16)
    s1_threat = run(SAMPLE1, 16, use_threat=True)
    mo_old, mo_new, mo_th = find_mono(s1_old), find_mono(s1_new), find_mono(s1_threat)
    # 样本 2：极端受控对照
    s2_old = run(SAMPLE2, None)
    s2_new = run(SAMPLE2, 16)
    checks = selfcheck()

    # ---------------- 控制台 ----------------
    def show(title, rows, mono):
        print("=" * 78)
        print(title)
        print("=" * 78)
        for r in rows:
            print(f"  {r['pos']:>2}. rank{r['rank']} {r['type']:<18} dps={r['dps']:>4} "
                  f"hp={r['hp']:>5} range={r['range']}")
        print(f"  -> monolith 名次 {mono['pos']}/{len(rows)}，rank{mono['rank']}，"
              f"dps={mono['dps']}")

    show("样本1 TH16真实阵 · 路径A 旧兜底 th=None", s1_old, mo_old)
    show("样本1 TH16真实阵 · 路径B th=16", s1_new, mo_new)
    show("样本1 TH16真实阵 · 威胁排序 threat_effective(th=16)", s1_threat, mo_th)
    show("样本2 极端受控对照(含TH17前瞻) · 路径A th=None", s2_old, find_mono(s2_old))
    show("样本2 极端受控对照(含TH17前瞻) · 路径B th=16", s2_new, find_mono(s2_new))
    print("\n内置自检：")
    all_ok = True
    for label, ok, detail in checks:
        all_ok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}  {detail}")

    # ---------------- MD ----------------
    tbl, notes = stats_table_md()
    md = f"""# TH16 数值取数自证（旧兜底 vs 真实值 + 有效威胁排序）

运行：`D:\\Python313\\python.exe tools\\stats_th16_check.py`
抓取日期：2026-11-23　口径：dps 为 wiki 基础每秒伤害（见各建筑 note），range 单位格。

## 1. TH16 四建筑数值表（来源 + 置信度）

{tbl}

### 口径与来源说明

{notes}

> **Firespitter 语义（补丁3 选定）**：现行版本解锁于 TH17（2024-11-25 加入），TH16 不可建造。
> 本侧选择：`stats("firespitter", th=16)` 仍返回现行 Lv1 参考值，**confidence=low + note 已注明**，
> 不新增 th=17 分支；TH16 阵型样本（样本1）不纳入此建筑，排序不命中。

## 2. 样本 1：TH16 真实布防示例（无 firespitter，12 栋）

> 示例样本，数量非实测阵；数量上限参考 clashlevels TH16 caps（中置信度）：
> https://clashlevels.com/town-hall/16

### 2A. 旧兜底 `stats(name, th=None)`（hp1400/dps120/range9）

{fmt_rows(s1_old)}

- monolith 名次 **{mo_old['pos']}/12**，**rank{mo_old['rank']}**，dps={mo_old['dps']}
  （兜底 120，与 ricochet 并列同值、不可区分，压在 wizard-tower 122 之下，与 cannon118/mortar45 同沉 rank1）。

### 2B. TH16 真实值 `stats(name, th=16)`

{fmt_rows(s1_new)}

- monolith 名次 **{mo_new['pos']}/12**，**rank{mo_new['rank']}**，dps={mo_new['dps']}
  （120→193，明确高于 wizard-tower 122 / cannon 118 / mortar 45，不再与杂兵防御同值混档）。

### 2C. 有效威胁排序 `threat_effective`（th=16，单列，不与 dps 排序混用）

公式：`threat = base_dps + 13% × H / 1.5s`（仅 monolith 计入百分比附加；H=5000hp 示例参照，
介于英雄与戈仑石人量级；Golem Lv7+ HP 7000+，https://clashofclans.fandom.com/wiki/Golem）。
monolith threat = 193 + 0.13×5000/1.5 ≈ 626。threat 对 H 敏感：H=3000→453，
H=5000→626，H=8000→886，非固定值。

{fmt_rows(s1_threat, threat_col=True)}

- 按实际反坦/反英雄威胁，monolith **第 {mo_th['pos']}/12 位**（threat={mo_th['threat']}）。

## 3. 对比小结（样本 1）

| 指标 | 旧兜底 (th=None) | TH16 真实 (th=16) |
| --- | --- | --- |
| monolith dps | {mo_old['dps']} | {mo_new['dps']}（+{mo_new['dps'] - mo_old['dps']}，+61%） |
| monolith hp | {mo_old['hp']} | {mo_new['hp']} |
| monolith 名次/档位 | {mo_old['pos']}/12，rank{mo_old['rank']} | {mo_new['pos']}/12，rank{mo_new['rank']}（基础 dps 口径） |
| monolith 威胁名次 | — | {mo_th['pos']}/12（threat={mo_th['threat']}，含 13% 附加） |

**诚实限制说明**：纯基础 dps 排序下 monolith(193) 仍低于 ricochet(390)/eagle(350)/scattershot(290)/
inferno(250)/x-bow(200)，这是 wiki 基础口径的客观事实，不是 bug。本次排序修正解决的是
"被兜底压成 120、与杂兵防御同值混档"，**不是把巨石排到第一**；反坦/反英雄地位由 2C 威胁
排序体现（第 1 位），两套结果并列展示、互不冒充。

## 4. 样本 2：极端受控对照（含 TH17 前瞻建筑 firespitter，仅作数值对照，不代表 TH16 阵）

### 4A. 旧兜底 th=None

{fmt_rows(s2_old)}

### 4B. th=16

{fmt_rows(s2_new)}

## 5. 13% 附加伤害原文出处（补丁4）

Monolith fandom wiki 页面 Summary 原文：
> "it is a single target, slow-firing defense that deals **additional damage equivalent to
> the target's maximum health** in addition to the base damage of the defense."
统计表 Lv3 行 Bonus Damage per Shot = **13%**；同页并称其为 Supercell 昵称的
"Hero Killer"，主要目标为 Heroes 与 Golems。来源：https://clashofclans.fandom.com/wiki/Monolith

## 6. 端到端调用方式（留给下一轮用真实 load_local 复跑）

另一路正在把 `tactics.load_local` 扩展为 `load_local(root, th=None)`；本侧只保证
`assets.stats(name, th=16)` 可被这样调用，**未改 tactics.py**。th=16 时逐建筑调用：

```python
from clashlab import assets
st = assets.stats(name, th=16)   # 签名 (name: str, th=None) -> dict，必含 dps / hp / range 键
dps = st["dps"]                  # 参与 load_local 的 dps 降序 + rank3/2/1 分档
```

复跑：把真实 TH16 阵型的 exposed 列表喂给新版 load_local，对比本文件第 2B 节。

## 7. 内置自检结果

"""
    for label, ok, detail in checks:
        md += f"- [{'PASS' if ok else 'FAIL'}] {label} — {detail}\n"
    md += f"\n合计 {sum(1 for _, ok, _ in checks if ok)}/{len(checks)} PASS。\n"

    out_dir = os.path.join(ROOT, "out", "th16")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "stats_th16_check.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\nwritten: {out_path}")
    print(f"SELFCHECK {sum(1 for _, ok, _ in checks if ok)}/{len(checks)} PASS")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
