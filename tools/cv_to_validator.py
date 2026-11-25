# -*- coding: utf-8 -*-
r"""P3a: 把 bases/th16/{01..06}/layout.json 转成 clash-of-clans-base-validator schema 并交叉验证。

只读 bases/ + 上游仓库；只写 out/overlay/_p3a/。
子命令：
  convert    生成 4 组 layout（2 坐标对齐口径 x 2 尺寸表）
  selfcheck  用我方 19 类定案尺寸表独立重算越界/重叠（A/B/C 三口径），作为对照基线
  validate   对每组 layout 跑上游 python -m coc_base validate --json，存 stdout + json
  summarize  汇总上游诊断 vs 我方自检，打印对照表（并写 summary.json）

复跑：
  D:\Python313\python.exe tools\cv_to_validator.py convert
  D:\Python313\python.exe tools\cv_to_validator.py selfcheck
  D:\Python313\python.exe tools\cv_to_validator.py validate
  D:\Python313\python.exe tools\cv_to_validator.py summarize
"""
import argparse
import json
import pathlib
import subprocess
import sys

# 我方定案 19 类占地表：来源 out/tactics/_convention/check_convention.py L24-30
# （仓内 assets.py STATS size + 仓内无 size 的 4 类外部 wiki 查证）。
OUR_FOOTPRINT = {
    "town-hall": 4, "eagle-artillery": 3, "scattershot": 3, "inferno-tower": 2,
    "x-bow": 3, "cannon": 3, "archer-tower": 3, "wizard-tower": 3,
    "air-defense": 3, "mortar": 3, "air-sweeper": 2, "hidden-tesla": 2,
    "bomb-tower": 3, "spell-tower": 2, "multi-archer-tower": 3,
    "monolith": 3, "firespitter": 3, "ricochet-cannon": 3, "clan-castle": 3,
}

# 2026-11-25：与仓内 assets.py STATS 自动同步，避免「两份尺寸表漂移」。
# 上游 ruleset(home-2026-11-17) + art manifest(width_tiles=1.994) 双证 spell_tower=2x2，
# 仓内与这里都已改；后续再改尺寸只需改 assets.py 一处。
try:
    _root = str(pathlib.Path(__file__).resolve().parents[1])
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from clashlab.assets import STATS as _ASSET_STATS
    for _k in list(OUR_FOOTPRINT):
        _sz = (_ASSET_STATS.get(_k) or {}).get("size")
        if isinstance(_sz, int) and _sz > 0:
            OUR_FOOTPRINT[_k] = _sz
except Exception:
    pass

# 我方 kebab 类型 -> 上游 catalogue 类型
TYPE_MAP = {
    "air-defense": "air_defense", "air-sweeper": "air_sweeper",
    "archer-tower": "archer_tower", "bomb-tower": "bomb_tower",
    "cannon": "cannon", "clan-castle": "clan_castle",
    "eagle-artillery": "eagle_artillery", "firespitter": "firespitter",
    "hidden-tesla": "hidden_tesla", "inferno-tower": "inferno_tower",
    "monolith": "monolith", "mortar": "mortar",
    "multi-archer-tower": "multi_archer_tower",
    "ricochet-cannon": "ricochet_cannon", "scattershot": "scattershot",
    "spell-tower": "spell_tower", "town-hall": "town_hall",
    "wizard-tower": "wizard_tower", "x-bow": "x_bow",
}
KEBAB_OF = {v: k for k, v in TYPE_MAP.items()}

ALIGNS = {"B": "center-grid", "C": "top-left"}  # 口径B / 口径C（见 convention_report 2.3）
VARIANTS = {"upstream": "用上游 ruleset 原尺寸", "ours": "用我方 19 类定案尺寸"}


def project_root():
    return pathlib.Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def dump_json(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upstream_dir(root):
    d = root / "out" / "overlay" / "_p3a" / "upstream" / "clash-of-clans-base-validator-main"
    if not d.is_dir():
        raise SystemExit("upstream 不存在，先下载: " + str(d))
    return d


def read_rules(root):
    return load_json(upstream_dir(root) / "rulesets" / "home-2026-11-17.json")


def topleft(tile_x, tile_y, size, align):
    """我方 tile（中心格）-> 上游 x/y（左上角）。"""
    if align == "B":  # 中心格 + 整数格 [x-(k-1)//2, x+(k-1)//2]
        r = (size - 1) // 2
        return tile_x - r, tile_y - r
    if align == "C":  # 上游坐标即左上角，直接取 tile 作左上
        return tile_x, tile_y
    raise SystemExit("unknown align " + align)


_SIZE_CACHE = {}


def size_for(up_kind, rules, variant):
    key = (up_kind, variant)
    if key not in _SIZE_CACHE:
        if variant == "ours":
            k = OUR_FOOTPRINT.get(KEBAB_OF.get(up_kind, up_kind))
            _SIZE_CACHE[key] = k if k is not None else rules["objects"][up_kind]["width"]
        else:
            _SIZE_CACHE[key] = rules["objects"][up_kind]["width"]
    return _SIZE_CACHE[key]


def make_ruleset(root, rules, variant):
    if variant == "upstream":
        return rules
    out = json.loads(json.dumps(rules))
    for kind in out["objects"]:
        kebab = KEBAB_OF.get(kind)
        if kebab in OUR_FOOTPRINT:
            out["objects"][kind]["width"] = OUR_FOOTPRINT[kebab]
            out["objects"][kind]["height"] = OUR_FOOTPRINT[kebab]
    return out


def build_layout(base_path, rules, align, variant):
    data = load_json(base_path)
    th = 16
    objects = []
    counts = {}
    for index, b in enumerate(data.get("buildings", [])):
        kind = b.get("type")
        if kind not in TYPE_MAP:
            raise SystemExit(str(base_path) + ": 未映射类型 " + repr(kind) + "，请补 TYPE_MAP")
        up_kind = TYPE_MAP[kind]
        k_up = size_for(up_kind, rules, variant)
        tx, ty = b["tile"]
        x, y = topleft(tx, ty, k_up, align)
        spec = rules["objects"][up_kind]
        max_level = spec["max_levels"].get(str(th), 0)
        level = max_level if max_level > 0 else 1
        settings = {}
        for key, options in spec.get("settings", {}).items():
            settings[key] = options[0]
        obj = {"id": "%s-%03d-%s" % (data.get("name", "base"), index, up_kind),
               "type": up_kind, "x": x, "y": y, "level": level}
        if settings:
            obj["settings"] = settings
        objects.append(obj)
        counts[up_kind] = counts.get(up_kind, 0) + 1
    counts.setdefault("town_hall", 1)
    return data, objects, counts


def cmd_convert(args):
    root = project_root()
    rules = read_rules(root)
    conv = root / "out" / "overlay" / "_p3a" / "converted"
    rulesets = conv / "rulesets"
    rulesets.mkdir(parents=True, exist_ok=True)
    for variant in VARIANTS:
        dump_json(rulesets / (variant + ".json"), make_ruleset(root, rules, variant))
    bases = sorted((root / "bases" / "th16").glob("*/layout.json"))
    if args.bases:
        wanted = set(args.bases)
        bases = [p for p in bases if p.parent.name in wanted]
    made = []
    for base_path in bases:
        nn = base_path.parent.name
        for align in ALIGNS:
            for variant in VARIANTS:
                d = conv / "layouts" / ("%s_%s_%s" % (nn, align, variant))
                d.mkdir(parents=True, exist_ok=True)
                data, objects, counts = build_layout(base_path, rules, align, variant)
                layout = {
                    "schema_version": 1,
                    "name": "th16_%s_%s_%s" % (nn, align, variant),
                    "town_hall": 16,
                    "village": "HV",
                    "ruleset_id": rules["id"],
                    "ruleset": "../../rulesets/%s.json" % variant,
                    "profile": "profile.json",
                    "design_notes": [
                        "P3a 转换自 bases/th16/%s/layout.json（只读）" % nn,
                        "align=%s variant=%s" % (align, variant),
                    ],
                    "objects": objects,
                }
                profile = {
                    "schema_version": 1,
                    "id": "th16-%s-%s-%s" % (nn, align, variant),
                    "ruleset_id": rules["id"],
                    "town_hall": 16,
                    "fully_developed": False,
                    "hero_hall_level": 0,
                    "bob_unlocked": False,
                    "crafted_phase": None,
                    "blocked_areas": [],
                    "inventory": dict(sorted(counts.items())),
                }
                dump_json(d / "layout.json", layout)
                dump_json(d / "profile.json", profile)
                made.append(str(d))
    print("converted:", len(made), "layout dirs under", conv)
    for m in made:
        print("  ", m)


# ---------------- 我方自检重算（口径 A/B/C，定案 19 类） ----------------
def cells_B(x, y, k):
    r = (k - 1) // 2
    return {(x + dx, y + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)}


def cells_BF(x, y, k):
    """口径B 的真实足迹版：左格 = x-(k-1)//2，宽 k 格（k=2 时占 2 格，不再是 cells_B 的 1 格）。"""
    left = x - (k - 1) // 2
    return {(left + dx, y - (k - 1) // 2 + dy) for dx in range(k) for dy in range(k)}


def cells_C(x, y, k):
    return {(x + dx, y + dy) for dx in range(k) for dy in range(k)}


def oob(cells):
    return any(cx < 0 or cy < 0 or cx >= 44 or cy >= 44 for cx, cy in cells)


def rect_A(x, y, k):
    h = k / 2.0
    return (x - h, y - h, x + h, y + h)


def oob_A(r):
    eps = 1e-6
    return r[0] < -eps or r[1] < -eps or r[2] > 44 + eps or r[3] > 44 + eps


def overlap_A(a, b):
    ix = min(a[2], b[2]) - max(a[0], b[0])
    iy = min(a[3], b[3]) - max(a[1], b[1])
    return ix > 0 and iy > 0


def cmd_selfcheck(args):
    root = project_root()
    out = root / "out" / "overlay" / "_p3a" / "converted" / "selfcheck.json"
    report = {}
    totals = {"A": 0, "B": 0, "BF": 0, "C": 0, "all3": 0}
    pair_counts = {"A": 0, "B": 0, "BF": 0, "C": 0}
    for base_path in sorted((root / "bases" / "th16").glob("*/layout.json")):
        nn = base_path.parent.name
        data = load_json(base_path)
        blds = [(b.get("type"), b["tile"][0], b["tile"][1]) for b in data.get("buildings", [])]
        entries = []
        for t, x, y in blds:
            k = OUR_FOOTPRINT.get(t)
            if k is None:
                entries.append({"type": t, "x": x, "y": y, "k": None})
                continue
            entries.append({"type": t, "x": x, "y": y, "k": k,
                            "oob_A": bool(oob_A(rect_A(x, y, k))),
                            "oob_B": bool(oob(cells_B(x, y, k))),
                            "oob_BF": bool(oob(cells_BF(x, y, k))),
                            "oob_C": bool(oob(cells_C(x, y, k)))})
        oob_lists = {}
        for key in ("A", "B", "BF", "C"):
            oob_lists[key] = [e for e in entries if e.get("oob_" + key)]
        all3 = [e for e in entries if e.get("oob_A") and e.get("oob_B") and e.get("oob_C")]
        pairs = {"A": [], "B": [], "BF": [], "C": []}
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                a, b = entries[i], entries[j]
                if a["k"] is None or b["k"] is None:
                    continue
                if overlap_A(rect_A(a["x"], a["y"], a["k"]), rect_A(b["x"], b["y"], b["k"])):
                    pairs["A"].append((a, b))
                if cells_B(a["x"], a["y"], a["k"]) & cells_B(b["x"], b["y"], b["k"]):
                    pairs["B"].append((a, b))
                if cells_BF(a["x"], a["y"], a["k"]) & cells_BF(b["x"], b["y"], b["k"]):
                    pairs["BF"].append((a, b))
                if cells_C(a["x"], a["y"], a["k"]) & cells_C(b["x"], b["y"], b["k"]):
                    pairs["C"].append((a, b))
        report[nn] = {
            "buildings": len(entries),
            "oob": {"A": len(oob_lists["A"]), "B": len(oob_lists["B"]),
                    "BF": len(oob_lists["BF"]), "C": len(oob_lists["C"]), "all3": len(all3)},
            "oob_objects": {key: oob_lists[key] for key in oob_lists},
            "overlap_pairs": {key: [
                {"a": {"type": p[0]["type"], "x": p[0]["x"], "y": p[0]["y"]},
                 "b": {"type": p[1]["type"], "x": p[1]["x"], "y": p[1]["y"]}}
                for p in pairs[key]] for key in pairs},
            "overlap_counts": {key: len(pairs[key]) for key in pairs},
        }
        for key in ("A", "B", "BF", "C"):
            totals[key] += report[nn]["oob"][key]
            pair_counts[key] += report[nn]["overlap_counts"][key]
        totals["all3"] += report[nn]["oob"]["all3"]
    report["_totals"] = {"oob": totals, "overlap_pairs": pair_counts,
                         "footprint_table": OUR_FOOTPRINT}
    dump_json(out, report)
    print("selfcheck ->", out)
    print("oob totals A/B/BF/C/all3 = %d/%d/%d/%d/%d" % (
        totals["A"], totals["B"], totals["BF"], totals["C"], totals["all3"]))
    print("overlap pairs A/B/BF/C = %d/%d/%d/%d" % (
        pair_counts["A"], pair_counts["B"], pair_counts["BF"], pair_counts["C"]))
    for nn in sorted(report):
        if nn.startswith("_"):
            continue
        r = report[nn]
        print(" ", nn, "oob", r["oob"], "pairs", r["overlap_counts"])


def cmd_validate(args):
    root = project_root()
    up = upstream_dir(root)
    conv = root / "out" / "overlay" / "_p3a" / "converted"
    reps = root / "out" / "overlay" / "_p3a" / "reports"
    reps.mkdir(parents=True, exist_ok=True)
    dirs = sorted((conv / "layouts").glob("*"))
    if args.bases:
        wanted = set(args.bases)
        dirs = [d for d in dirs if d.name.split("_")[0] in wanted]
    results = []
    for d in dirs:
        layout = d / "layout.json"
        variant = d.name.split("_")[-1]
        ruleset = (conv / "rulesets" / (variant + ".json")).resolve()
        out_json = reps / (d.name + ".validation.json")
        proc = subprocess.run([sys.executable, "-m", "coc_base", "validate", str(layout),
                               "--ruleset", str(ruleset), "--json", str(out_json)],
                              cwd=str(up), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        (reps / (d.name + ".stdout.txt")).write_text(proc.stdout + proc.stderr, encoding="utf-8")
        results.append({"run": d.name, "exit": proc.returncode,
                        "stdout_path": str(reps / (d.name + ".stdout.txt")),
                        "json_path": str(out_json), "exists": out_json.exists()})
        print("%-28s exit=%s json=%s" % (d.name, proc.returncode, out_json.exists()))
    dump_json(reps / "validate_index.json", results)


def cmd_summarize(args):
    root = project_root()
    base = root / "out" / "overlay" / "_p3a"
    sc = load_json(base / "converted" / "selfcheck.json")
    summary = {"selfcheck_totals": sc["_totals"], "runs": {}}
    for run in sorted((base / "converted" / "layouts").glob("*")):
        name = run.name
        json_path = base / "reports" / (name + ".validation.json")
        if not json_path.exists():
            continue
        v = load_json(json_path)
        codes = {}
        for d in v.get("diagnostics", []):
            codes.setdefault(d["code"], []).append(d)
        summary["runs"][name] = {
            "status": v["status"], "errors": v["errors"], "unknowns": v["unknowns"],
            "placed_counts": v["placed_counts"], "occupied_tiles": v["occupied_tiles"],
            "codes": {k: len(val) for k, val in sorted(codes.items())},
            "overlap_messages": [d["message"] for d in codes.get("OVERLAP", [])],
            "boundary_messages": [d["message"] for d in codes.get("BOUNDARY", [])],
            "diagnostics": v["diagnostics"],
        }
    dump_json(base / "converted" / "summary.json", summary)
    print("summary ->", base / "converted" / "summary.json")
    for name in sorted(summary["runs"]):
        r = summary["runs"][name]
        print("%-28s %-9s err=%d unk=%d OVERLAP=%d BOUNDARY=%d" % (
            name, r["status"], r["errors"], r["unknowns"],
            r["codes"].get("OVERLAP", 0), r["codes"].get("BOUNDARY", 0)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("convert", cmd_convert), ("selfcheck", cmd_selfcheck),
                     ("validate", cmd_validate), ("summarize", cmd_summarize)):
        p = sub.add_parser(name)
        p.add_argument("--bases", nargs="*", help="只处理这些阵号，如 01 03")
        p.set_defaults(func=fn)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
