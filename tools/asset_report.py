# -*- coding: utf-8 -*-
# asset_report.py — 汇总 asset_raw_l2/b14 + truth，出 CSV 与 MD 报告
import os, json, csv
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
REC = os.path.join(ROOT, "out", "recog")

l2 = json.load(open(os.path.join(REC, "asset_raw_l2.json"), encoding="utf-8"))
b14 = json.load(open(os.path.join(REC, "asset_raw_b14.json"), encoding="utf-8"))
truth_l2 = json.load(open(os.path.join(REC, "truth_l2.json"), encoding="utf-8"))
truth_b14 = json.load(open(os.path.join(REC, "truth_b14.json"), encoding="utf-8"))

ORDER = ["townhall","airdef","eagle","scatter","inferno","xbow","mortar","bombtower",
         "sweeper","tesla","wiztower","archertower","cannon","multiarcher",
         "firespitter","monolith","spelltower","storage","collector","wall"]
CN = {
 "townhall":"大本营","airdef":"防空火箭","eagle":"鹰炮","scatter":"散射炮",
 "inferno":"地狱塔","xbow":"X连弩","mortar":"迫击炮","bombtower":"炸弹塔",
 "sweeper":"空气炮","tesla":"隐形特斯拉","wiztower":"法师塔","archertower":"箭塔",
 "cannon":"加农炮","multiarcher":"多弓箭塔","firespitter":"喷火塔","monolith":"巨石碑",
 "spelltower":"法术塔","storage":"资源仓(金/水/黑)","collector":"收集器(金/水/黑)","wall":"城墙条",
}

def fail_reason(t, peak):
    if peak is None:
        return "无模板来源：wall条无alpha且带草地底，gmax=0"
    return "颜色相近：CCORR仅比亮度相关，草皮/墙/UI与建筑同被打≥0.75饱和，无形状/颜色约束"

rows = []
for t in ORDER:
    r = l2["results"].get(t, {})
    tb = truth_l2["manual_anchors"].get(t, {})
    tn = tb.get("count_visible")
    note = tb.get("note", "")
    # 人工核实：无任一命中框压在同类真建筑上 → 查准0；有真值的类查全0
    recall = 0.0 if (tn is not None and tn > 0) else "n/a"
    precision = 0.0
    rows.append({
        "type": t, "cn": CN[t],
        "peak_l2": r.get("best_peak"), "hits_l2": r.get("n_hits"),
        "truth_l2": tn if tn is not None else "不可辨/未见",
        "scale_l2": r.get("best_scale"), "tpl_l2": (r.get("best_tpl") or "").split("/")[-1],
        "sat_l2": r.get("sat_frac75"),
        "peak_b14": b14["results"][t]["best_peak"],
        "hits_b14": b14["results"][t]["n_hits"],
        "scale_b14": b14["results"][t]["best_scale"],
        "verdict": "不过(无峰)" if r.get("best_peak") is None else "不过(饱和误报)",
        "recall": recall, "precision": precision,
        "reason": fail_reason(t, r.get("best_peak")),
        "note": note,
    })

# CSV
csvp = os.path.join(REC, "recog_asset_l2.csv")
with open(csvp, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["类型","中文","L2峰值","L2命中数","L2真值(人工)","查全","查准","L2最优尺度","L2模板","饱和占比",
                "b14峰值","b14命中数","b14最优尺度","判定","失败原因","备注"])
    for x in rows:
        w.writerow([x["type"],x["cn"],x["peak_l2"],x["hits_l2"],x["truth_l2"],x["recall"],x["precision"],
                    x["scale_l2"],x["tpl_l2"],x["sat_l2"],x["peak_b14"],x["hits_b14"],x["scale_b14"],
                    x["verdict"],x["reason"],x["note"]])
print("csv saved", csvp)

# MD
passed = sum(1 for x in rows if x["verdict"].startswith("过"))
md = []
md.append("# 官方RGBA素材 alpha-mask 多尺度匹配报告（最大档分块 + 侦察帧对比）\n")
md.append("## 帧清单（盘上核实真实路径）\n")
md.append("| 角色 | 真实路径 | 尺寸 |\n|---|---|---|\n")
md.append("| 最大档分块×15 | `out/overlay/blocks/b00.png … b14.png` | 950×550 |\n")
md.append("| 15块拼接图 | `out/overlay/v6_stitched_base.png` | 5307×2667（未重跑，作留档） |\n")
md.append("| 金仓最大档 | `out/overlay/ladder/maxzoom_building.png` | 1280×720 |\n")
md.append("| 墙段最大档 | `out/overlay/ladder/maxzoom_wall.png` | 1280×720（与buildings同帧） |\n")
md.append("| 侦察干净帧 | `out/overlay/enemy/b14_full.png` | 870×494 |\n")
md.append("| 盟友整屏(未跑) | `out/overlay/full/v12_army_full.png` | 1280×720 RGBA |\n")
md.append("\n## 方法\n")
md.append("- 模板：`assets/coc/buildings/<type>/level-*.png` 全部等级图作候选，alpha>40 当 mask，仅比建筑本体。\n")
md.append("- 匹配：`TM_CCORR_NORMED` + mask；bandA 0.60–1.40 步0.05（最大档），bandB 0.20–0.60 步0.03（侦察帧）。\n")
md.append("- NMS IoU 0.3；阈值 peak>0.75；每类保留 top30。\n")
md.append("- 输入：L2=`out/overlay/blocks/b00..b14.png`（80px/格，己方村庄采集带）；侦察帧=`out/overlay/enemy/b14_full.png`（~18px/格）。\n")
md.append("\n## tile_px 复测（硬真值，独立于工具）\n")
md.append("| 判据 | 测量 | px/格 |\n|---|---|---|\n")
md.append("| 金仓3×3底面 W/3（maxzoom_building y500-510带，旧独立记录250px） | 250/3 | 83 |\n")
md.append("| 墙白帽间距（NE带4帽3间隔，78.4/77.6/72.7中位） | 77 |\n")
md.append("| **采用值** | 区间77–83，**取80px/格** |\n")
md.append("> 本轮程序行扫被邻墙/土路干扰未复现83；采用 ladder/maxzoom_measure.md 独立记录，方法已登记。\n")
md.append("\n## L2 最大档逐类表（bandA）\n")
md.append("| 类型 | 峰值 | 命中数 | 人工真值 | 查全 | 查准 | 最优尺度 | 模板 | 判定 | 失败原因 |\n|---|---|---|---|---|---|---|---|---|---|\n")
for x in rows:
    md.append(f"| {x['cn']}({x['type']}) | {x['peak_l2']} | {x['hits_l2']} | {x['truth_l2']} | {x['recall']} | {x['precision']} | {x['scale_l2']} | {x['tpl_l2']} | {x['verdict']} | {x['reason']} |\n")
md.append("\n## 侦察帧 b14 对比（bandB）\n")
md.append("| 类型 | 峰值 | 命中数 | 最优尺度 |\n|---|---|---|---|\n")
for x in rows:
    md.append(f"| {x['cn']}({x['type']}) | {x['peak_b14']} | {x['hits_b14']} | {x['scale_b14']} |\n")
md.append("\n## 饱和证据（CCORR_NORMED 无判别力的直接证据）\n")
md.append("- L2 各类峰值 0.858–0.936，侦察帧 0.872–0.938，全部 >0.75 阈值；\n")
md.append("- 饱和占比 sat_frac75（≥0.75像素占比）L2 0.27–0.57，侦察帧 0.46–0.77——画面过半区域都过阈值；\n")
md.append("- 最优尺度偏向 s=1.4（最大模板）或 s=0.6（最小模板），无真实尺度收敛；\n")
md.append("- 人眼核对：L2 命中框散布在草地/墙/UI，无一压在同类真建筑上（见 recog_asset_l2.png）。\n")
md.append("\n## 附：masked CCOEFF_NORMED 诊断（非锁定判据，仅定位根因）\n")
md.append("| 类型 | 锚块 | CCOEFF峰值 | 落点 | 结论 |\n|---|---|---|---|---|\n")
md.append("| wiztower | b10 | 0.607 | (416,314) 近中央法师塔 | 唯一接近锚点，但<0.75阈值 |\n")
md.append("| wiztower | b05 | 0.683 | (553,423) 右侧收集器 | 误报 |\n")
md.append("| mortar | b09 | 0.516 | (508,62) 右缘 | 误报 |\n")
md.append("| airdef | b10 | 0.439 | (758,95) 近黄黑塔 | 分不足 |\n")
md.append("| airdef | b11 | 0.505 | (590,342) | 误报 |\n")
md.append("> CCOEFF 去均值后峰值落到0.44–0.68，说明渲染差异确实压低相关；CCORR饱和是归一化口径问题，换CCOEFF+颜色余弦+几何校验才有分类可能。\n")
md.append("\n## 未跑输入说明\n")
md.append("- `out/overlay/full/v12_army_full.png`（盟友整屏）本轮未跑：锁定判据在L2/侦察帧已饱和，换帧不改变方法结论；留待CCOEFF管线复测。\n")
md.append("\n## 污染区域报告（最大档帧，禁匹配区）\n")
md.append("| 块/区 | 坐标(块内) | 污染物 |\n|---|---|---|\n")
poll = [
 ("全块右缘","x≈905–950","绿色+按钮竖排（UI）"),
 ("b00","底部居中","5小时24分钟建造计时条；右下蓝龙troop；左上铭牌“锤”；左侧木柴堆"),
 ("b02","顶部居中","5小时23分钟计时；紫宝石气泡；暗营建筑"),
 ("b05","顶部/左侧","紫宝石气泡；金币气泡；紫皮宠物；+按钮"),
 ("b09","左上/左缘","金币气泡；左缘金矿发光体"),
 ("b10","左缘/顶部","“95”数字气泡；右上骷髅气球；+按钮"),
 ("b11","中部","骷髅气球装饰；木箱"),
 ("b13","右下/顶部","红骷髅气球簇压徽章周边；6天17小时计时条；右上锁定徽章；+按钮"),
 ("b14","顶部/右下","“小砸锤”铭牌；红气球；骷髅气球；+按钮"),
 ("maxzoom_building(ladder)","顶部/左上/左下/右下","资源条+2天14小时计时；142级TH徽章面板；左下战斗面板；右下建造/免费!按钮；红气球压金仓左上"),
]
for a,b,c in poll:
    md.append(f"| {a} | {b} | {c} |\n")
md.append("\n## 天花板结论\n")
md.append("1. **不是分辨率问题**：最大档80px/格下3×3建筑≈240px，素材本体清晰，但 masked CCORR_NORMED 仍全帧饱和（0.86–0.94），峰值无判别力；\n")
md.append("2. 根因：官方3D渲染与实机截屏在光照/视角/LOD上存在系统差异，CCORR只比亮度相关，不约束形状/颜色分布，故背景草皮也能出高分；\n")
md.append("3. 要分类必须换判别特征：masked CCOEFF（均值归零）+ 颜色余弦 + 几何长宽比，或分割提案后做颜色/形状特征分类；裸 CCORR 直匹配在任何 tile_px 下都不成立；\n")
md.append("4. 物理尺寸参考：3×3=240px@80格、4×4=320px@80格；侦察帧~18px/格时3×3仅54px、2×2仅36px，小塔物理不足。\n")
md.append("\n## 计数\n")
md.append(f"- L2 最大档通过：**{passed}/20 类**（含资源/墙）；防御18类通过 0/18。\n")
md.append("- 侦察帧对比：全部饱和，0 类锁定。\n")

outmd = os.path.join(REC, "recog_asset_report.md")
open(outmd, "w", encoding="utf-8").write("".join(md))
print("md saved", outmd)
