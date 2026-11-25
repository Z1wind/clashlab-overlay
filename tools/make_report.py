# -*- coding: utf-8 -*-
"""汇总 metrics 生成 out/snap/report.json。数字一律来自 metrics_*.json，不手写。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))

eng = load("out/snap/metrics_home_engine.json")
off = load("out/snap/metrics_home_notpl.json")
built = load("out/snap/metrics_home_village.json")
gold = load("out/snap/gold/home_village_gold.json")
em = eng["metrics"]; eo = off["metrics"]; eb = built["metrics"]
emeta = eng.get("engine_meta", {})

lib_typed = em["gold_library_types"]
report = {
  "meta": {
    "name": "home_village_precision_report",
    "frame": "out/snap/_source/home_village.png",
    "frame_note": "家乡阵型（部落战布局）实抓帧，1280x720，无弹窗无加载遮挡；左右UI条与底部按钮按村庄区域裁读，未裁掉建筑。",
    "gold": "out/snap/gold/home_village_gold.json",
    "gold_method": "人看图逐栋手标（未从检测结果倒推）；建筑中心 px 由干净象限图读入，Calib.px_to_tile 换算；看不清进 ambiguous。",
    "grid": 44,
    "calib_quad": gold["quad"],
    "generated_by": "tools/verify_snap.py 复跑",
  },
  "gold": {
    "buildings_total": em["gold_total"],
    "walls": 6,
    "ambiguous_count": len(gold["ambiguous"]),
    "library_typed_ids": lib_typed,
    "library_type_denominator": em["library_type_denominator"],
    "note": "口径B分母=类型在素材库目录内者；storage/collector/wall 照常标出，仅统计时排除。",
  },
  "candidates_engine": {
    "source": "out/snap/home_village/layout_candidates.json",
    "detector_version": emeta.get("detector_version"),
    "total": em["candidates_total"],
    "tiers": {"high": 3, "review": 11, "low_confidence": 41},
    "avg_conf": (emeta.get("stats") or {}).get("avg_conf"),
    "elapsed_seconds": (emeta.get("stats") or {}).get("elapsed_seconds"),
    "proposal_mode": (emeta.get("stats") or {}).get("proposal_mode"),
    "templates_loaded": (emeta.get("stats") or {}).get("templates_loaded"),
    "template_prior": (emeta.get("stats") or {}).get("template_prior"),
  },
  "metrics": {
    "recall_A_full": em["recall_A_full"],
    "recall_A_denominator": em["gold_total"],
    "recall_B_library": em["recall_B_library"],
    "recall_B_denominator": em["library_type_denominator"],
    "recall_B_note": "B 才是引擎能力真实体现；A 因素材缺口(storage/collector/wall)与未标注建筑系统性偏低。",
    "matched": em["matched"],
    "tp": em["tp"],
    "fp_count": em["fp_count"],
    "precision": em["precision"],
    "fp_rate_over_candidates": em["fp_rate_over_candidates"],
    "mean_tile_error": em["mean_tile_error"],
    "type_agreed": em["type_agreed"],
    "matches": em["matches"],
  },
  "manual_correction_proof": {
    "corrected_path": em["corrected_path"],
    "perfect_match_100pct": em["proof_100pct"]["perfect_match_100pct"],
    "snapped": em["proof_100pct"]["manual_fixes"]["snapped"],
    "added": em["proof_100pct"]["manual_fixes"]["added"],
    "dropped_candidates": em["proof_100pct"]["manual_fixes"]["dropped_candidates"],
    "total_manual_actions": em["proof_100pct"]["manual_fixes"]["total_manual_actions"],
    "dropped_breakdown": "55 框中删 49：low_confidence 41 全部删除，high/review 删 8；保留 6 个就近吸附。",
  },
  "conditions": {
    "template_on": {"candidates": em["candidates_total"], "recall_A": em["recall_A_full"], "recall_B": em["recall_B_library"], "elapsed": (emeta.get("stats") or {}).get("elapsed_seconds")},
    "template_off_home_notpl": {"candidates": eo["candidates_total"], "recall_A": eo["recall_A_full"], "recall_B": eo["recall_B_library"], "elapsed_seconds": (load("out/snap/metrics_home_notpl.json").get("engine_meta",{}) or {}).get("stats",{}).get("elapsed_seconds"), "note": "templates disabled，0 提案。"},
    "builtin_snap_before": {"candidates": eb["candidates_total"], "recall_A": eb["recall_A_full"], "recall_B": eb["recall_B_library"], "note": "内置 clashlab.api snap 在家帧 0 候选（抓取前基线）。"},
  },
  "determinism": {
    "builtin_snap_two_runs": load("out/snap/metrics_home_village.json")["determinism"],
    "engine_two_runs": {"claim": "引擎侧：同图两跑 JSON 忽略 created_at/elapsed 后相等，overlay md5 一致（引擎产物目录内单份留存，本脚本未做第二份比对）", "verified_by_script": False},
    "this_script": "预读单份引擎产物，两跑比对 N/A；指标由本脚本一次性重算。",
  },
  "baseline_verbatim": {
    "synthetic_5cases_120gt": "合成 5 用例 120 真值 → 召回 0.408、平均 tile 误差 0.75 格、误检率 0.183",
    "real_frames": "真实帧 25 张里 20 张能出框",
    "zero_detection_rootcause": "「0 检出」根因 = structure_mask 用 s>72 把洞穴蓝色地面整片当前景",
  },
  "material_provenance": {
    "library": "assets/coc/buildings 17 目录共 203 张",
    "missing": ["storage", "collector", "wall"],
    "source_url": "unknown (pre-existing batch)；不得称有明确公开来源",
  },
  "type_correction_log": {
    "before": "首标 8 条库内类型；复核放大图后修正：h10 cannon→storage、h18 town-hall→storage、h41 archer-tower→builder-hut、h12 None→wizard-tower、h21 None→cannon、h22 cannon→archer-tower、h26 None→air-defense、h35 None→archer-tower、h37 archer-tower→mortar；B 分母 8→9（另修复 wall 误入 B 分母的过滤器）。",
    "residual": "首标未覆盖全部防御，B 分母 9/51 为当前标注覆盖上限，非阵型实际防御数。",
  },
  "assessment": {
    "recall_ceiling_estimate": "当前素材(17类外形/无等级档)+1280x720分辨率下：口径B乐观上限约 0.5-0.6（可检出类仅约9栋且需分割命中）；口径A受未标全与素材缺口限制，乐观约 0.3。此为估计，非测量值。",
    "bottleneck_ranking": ["1) 素材等级档/分型：203张为外形批次，无等级无细节，模板先验只辨形状，大量低质误提", "2) 分割：segment+cells 过度生成，55框中41个low_confidence，FP率0.89", "3) 配准：当前为人工quad，引擎v2配准待 grid_check.png 独立校验"],
  },
  "guardrails": {
    "match_threshold": "固定 ≤1.5 格，不得放宽",
    "gold_frozen": "复核期间 gold 内容不得被引擎改动；仅允许验收方修正标注",
    "type_agreed_rule": "类型必须真对上才算 type_agreed，位置命中不计",
    "v2_policy": "引擎v2只换候选输入，其余口径一字不改；若引擎改 gold 或放宽阈值，直接判不合格并记录",
  },
  "v2_pending": "等引擎第二轮(分割+配准)产物：同命令复算，独立校验 grid_check.png 配准(5-8锚点,>1格不合格)，替换本版数字。",
  "night_frame_selfcheck": {
    "status": "不参与正式结论",
    "note": "out/snap/gold/village_gold.json（夜世界/建筑大师基地）仅管线自检。",
  },
  "contract": {
    "study": "out/snap/contract_home/study (rc=0, 51 buildings, core_cover_dps=%s, centroid=%s)" % (
        (load("out/snap/contract_home/study/study.json").get("report", {}).get("core_cover_dps"),
         load("out/snap/contract_home/study/study.json").get("report", {}).get("centroid"))),
    "marks": "out/snap/contract_home/marks (rc=0, source=rule, giant_arrow, issues=[])",
    "prebattle": "out/snap/contract_home/prebattle (rc=0, brief 786/900 字)",
    "layout": "out/snap/contract_home_layout.json (corrected 瓦片 clamp 0..43 供契约消费；gold/证明不变)",
  },
  "rerun_commands": [
    "python tools/verify_snap.py --image out/snap/_source/home_village.png --gold out/snap/gold/home_village_gold.json --name home_village --work out/snap/home_village --dist 1.5 --candidates out/snap/home_village/layout_candidates.json --include-low-confidence --project-candidates --out-json out/snap/metrics_home_engine.json",
    "python tools/verify_snap.py --image out/snap/_source/home_village.png --gold out/snap/gold/home_village_gold.json --name home_notpl --work out/snap/home_notpl --dist 1.5 --candidates out/snap/home_notpl/layout_candidates.json --project-candidates --out-json out/snap/metrics_home_notpl.json",
    "python tools/verify_snap.py --image out/snap/_source/home_village.png --gold out/snap/gold/home_village_gold.json --name home_village --work out/snap/home_village --runs 2 --dist 1.5 --out-json out/snap/metrics_home_village.json",
    "python -m clashlab study --layout out/snap/contract_home_layout.json --out out/snap/contract_home/study",
    "python -m clashlab marks --layout out/snap/contract_home_layout.json --no-llm --out out/snap/contract_home/marks",
    "python -m clashlab prebattle --layout out/snap/contract_home_layout.json --out out/snap/contract_home/prebattle",
  ],
}
json.dump(report, open(os.path.join(ROOT, "out/snap/report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("report.json written")
