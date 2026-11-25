# 建筑模板可用性探针报告 (_probe_template.py)

- 参考截图: `out\audit\run_a1\frame_001.png`（home village (disconnect dialog overlay)）, `out\grab2\grab_1795414594.png`（builder base, clean）, `out\analyze\analyze.png`（builder base, planning panel overlay）
- 模板: 203 张既有批次；方法: alpha 裁主体 + alpha mask 加权 TM_CCORR_NORMED(BGR)，多尺度 [0.15, 0.2, 0.25, 0.35, 0.45, 0.6, 0.8, 1.0]，NMS 15px
- 阳性对照: 模板自身粘贴回画面，masked CCORR 可精确定位(0.92-0.97)；无 mask 的 CCOEFF 只能到 0.56-0.69 且定位偏移，故本探针采用 mask 版
- 阈值: 命中 ≥0.6，区分差 home-bb ≥0.15

## 总体结论: **暂不定论 (inconclusive: 阴性帧仅夜世界、家乡帧被弹窗遮挡，需家乡帧复测)**
- 可用白名单 (0): 无
- 存疑 (17): airdef, archertower, bombtower, cannon, eagle, firespitter, inferno, monolith, mortar, multiarcher, scatter, spelltower, sweeper, tesla, townhall, wiztower, xbow
- 不可识别黑名单 (0): 无

## 分类型汇总
| type | n | home_best | bb_best | gap | home命中 | bb误命中 | 判定 |
|---|---|---|---|---|---|---|---|
| airdef | 16 | 0.854 | 0.869 | -0.015 | 16 | 16 | ambiguous |
| archertower | 21 | 0.890 | 0.902 | -0.012 | 21 | 21 | ambiguous |
| bombtower | 13 | 0.891 | 0.900 | -0.009 | 13 | 13 | ambiguous |
| cannon | 21 | 0.910 | 0.906 | 0.004 | 21 | 21 | ambiguous |
| eagle | 7 | 0.881 | 0.885 | -0.004 | 7 | 7 | ambiguous |
| firespitter | 3 | 0.841 | 0.853 | -0.011 | 3 | 3 | ambiguous |
| inferno | 12 | 0.867 | 0.882 | -0.015 | 12 | 12 | ambiguous |
| monolith | 5 | 0.903 | 0.899 | 0.004 | 5 | 5 | ambiguous |
| mortar | 18 | 0.887 | 0.896 | -0.010 | 18 | 18 | ambiguous |
| multiarcher | 4 | 0.867 | 0.864 | 0.003 | 4 | 4 | ambiguous |
| scatter | 7 | 0.914 | 0.907 | 0.006 | 7 | 7 | ambiguous |
| spelltower | 4 | 0.899 | 0.896 | 0.003 | 4 | 4 | ambiguous |
| sweeper | 7 | 0.847 | 0.868 | -0.021 | 7 | 7 | ambiguous |
| tesla | 17 | 0.873 | 0.874 | -0.000 | 17 | 17 | ambiguous |
| townhall | 18 | 0.895 | 0.944 | -0.048 | 18 | 18 | ambiguous |
| wiztower | 17 | 0.947 | 0.931 | 0.016 | 17 | 17 | ambiguous |
| xbow | 13 | 0.881 | 0.882 | -0.001 | 13 | 13 | ambiguous |

## 附注
- 本探针只覆盖探针运行时已有的 203 张既有批次；后补的 storage/collector（16 张）与 wall strip（1 张）未参与本轮测试。
- 阳性对照：把模板自身粘贴回画面，masked CCORR_NORMED 可精确定位（0.92–0.97），说明管线本身可工作；无 mask 的 CCOEFF 只能到 0.56–0.69 且定位偏移，故下游不宜直接使用裸 CCOEFF。

## 家帧复测结论（2026-11-23，干净家乡帧 home_village.png）

**帧**：`out/snap/_source/home_village.png`（1280×720，无弹窗无遮罩）。
**tile_px=16.36**（取自 `out/snap/home_village/run1|run2|cond_atlas_on` 的 `detect_meta.tile_px`；主 `layout_candidates.json` 的 detect_meta 为 null）。
**方法**：期望尺寸 = `w_tiles/h_tiles × tile_px`，缩放 0.8–1.2（±20%），CCOEFF_NORMED；仅扫 ROI（150,55,1150,615，排除侧栏与底部按钮栏）；阴性帧 `out/live_00.png`。
**判定规则**：whitelist = home_best≥0.60 且压在真实建筑上且 margin≥0.15；blacklist = home_best<0.55 或 margin≤0；unverified = 中间地带。

| type | L | home_best | neg_best | margin | verdict |
|---|---|---|---|---|---|
| airdef | 1 | 0.571 | 0.654 | -0.083 | blacklist |
| archertower | 16 | 0.560 | 0.607 | -0.046 | blacklist |
| bombtower | 2 | 0.527 | 0.669 | -0.142 | blacklist |
| cannon | 12 | 0.570 | 0.707 | -0.137 | blacklist |
| collector | 12 | 0.577 | 0.628 | -0.051 | blacklist |
| eagle | 6 | 0.527 | 0.644 | -0.117 | blacklist |
| firespitter | 1 | 0.511 | 0.563 | -0.052 | blacklist |
| inferno | 6 | 0.548 | 0.618 | -0.070 | blacklist |
| monolith | 1 | 0.543 | 0.641 | -0.098 | blacklist |
| mortar | 2 | 0.550 | 0.642 | -0.092 | blacklist |
| multiarcher | 3 | 0.526 | 0.539 | -0.013 | blacklist |
| scatter | 4 | 0.585 | 0.577 | +0.009 | unverified |
| spelltower | 1 | 0.554 | 0.699 | -0.145 | blacklist |
| storage | 7 | 0.632 | 0.596 | +0.036 | unverified |
| sweeper | 2 | 0.580 | 0.703 | -0.123 | blacklist |
| tesla | 10 | 0.579 | 0.651 | -0.072 | blacklist |
| townhall | 4 | 0.590 | 0.655 | -0.066 | blacklist |
| wiztower | 7 | 0.626 | 0.686 | -0.060 | blacklist |
| xbow | 10 | 0.518 | 0.603 | -0.085 | blacklist |
| wall (strip) | 14 | 0.283 (CCOEFF) | — | — | unverified |

**白名单**：无。**黑名单（逐像素直匹配不成立）**：airdef、archertower、bombtower、cannon、collector、eagle、firespitter、inferno、monolith、mortar、multiarcher、spelltower、sweeper、tesla、townhall、wiztower、xbow。**未验证**：scatter、storage、wall。

**人眼核对**：各类型最佳峰值落点均不在对应建筑上（抽样：storage 峰值落在底部 UI/草地边、wiztower 落在右上资源条、xbow 落在一座深色塔周围）；masked CCORR 在家帧同样饱和（0.83–0.94 无区分），边缘 CCOEFF 全部 <0.25，宽尺度 CCOEFF 扫描 home 仍不高于阴性帧。

**墙带**：`wall_l14_strip.png` 带草地底，CCORR 0.939（草地伪高分）、CCOEFF 0.283 无区分力，wall 不入白名单。

**结论**：这批渲染图与实机捕获画面在视角/光照/LOD 上差异明显，**逐像素模板直匹配不能作为家乡帧识别主路径**（无类型达白门框）。素材本身清晰透明，仍可作类型分类参考图库/颜色与造型手册；下游建议改走「分割提案 + 颜色/形状特征」或引擎自有时序候选，不要把这批 PNG 当主路径模板。注意：blacklist 仅否定"直匹配方法"，不等于素材作废。

## 引擎实现交叉核查（2026-11-23，针对 airdef/archertower/cannon/inferno/xbow 五类）

**起因**：引擎自测记录称家帧模板最高分 0.767、55 框且命中真建筑，与上一轮探针「home_best≤阴性帧、无白名单」结论冲突。本轮只读调用 `clashlab/template_match.py` 的 `TemplateBank`（未修改），在同一 `home_village.png` 上重跑。

**直接调用 scan() 结果**：13 框（storage×6、wizard-tower×4、archer-tower×3），max 0.762（storage 家族），与记录的 0.767 同量级；五类中仅 archer-tower 出框，airdef/inferno/xbow/cannon 零出框。逐框人眼核对：13 框仅约 1 框可能压在同类建筑，其余落在资源条 UI、部落城堡旗帜、深色巨碑、火龙空位等。

**五类 raw top 峰值（引擎内部循环口径，掩膜 CCOEFF + 几何/颜色 +0.03）**：

| 类型 | 代表档 | home best(raw) | 峰值落点 | 压在同类建筑 |
|---|---|---|---|---|
| airdef | L9 | 0.471 | (455,182) 金堆/城墙角 | no |
| archertower | L11 | 0.641 | (710,408) 黄黑炮台 | no（非箭塔） |
| cannon | L11 | 0.539 | (228,281) 金色收集器 | no |
| inferno | L7 | 无 ≥0.40 峰值 | — | no |
| xbow | L7 | 0.417 | (743,267) 深色巨碑 | no |

**防空塔单独计数（人眼逐座 6× 放大核对）**：实帧 **4 座**防空（约 (330,215)/(1050,385)/(360,490)/(692,650)，黄黑条纹塔身+粉紫发光芯）；引擎 scan() 识别 **0** 座，我方上一轮方法识别 **0** 座。两边独立同数，无分歧。

**方法差异（我方上一轮 vs 引擎）**：
1. 掩膜：引擎 alpha>40 掩膜 CCOEFF，我方灰度裸 CCOEFF 无掩膜——但引擎带掩膜仍偏离真建筑，掩膜非失败主因；
2. 引擎有 aspect(±0.38) + BGR 颜色余弦(tol 0.45) 双校验各 +0.03；我方无；
3. 代表档：引擎取中位 level 单档，我方逐档扫；尺度集引擎 {0.85,1.0,1.18}，我方 0.8~1.2；
4. ROI：引擎默认 (179,100,1126,619)，我方 (150,55,1150,615)，引擎峰值仍漏进右上资源条 UI；
5. 阈值：引擎 min_score 0.60 + NMS，我方 home-vs-neg margin 排序。

**裁定 (a)：素材本身不适配实机渲染**，不是 (b) 我方上一轮方法缺陷。引擎完整管线（掩膜+几何+颜色+NMS）同样把五类峰值打到非同类/UI/空地，airdef 4 座零召回；上一轮黑名单维持不变，不改口。引擎自测 0.767/55 框记录用现行代码复现为 0.762/13 框且多数离类，「命中落在真建筑」未复现，疑为旧配置/旧代表档或 template_prior blob 打分口径，现行源码无对应分支。明细见 `probe_home_crosscheck.json`。

## 说明（结论有前提，勿整体否定素材）
- **本批素材是家乡（home）外观；阴性参考帧 bb_* 全部来自夜世界（建筑大师基地），跨基地本就不应高分，不能据此判素材不可用。**
- home_dialog 帧中央被断线弹窗大面积遮挡，可见家乡建筑只在四周边缘，home_best 偏保守。
- 本探针在夜世界帧上 17 类全部 ambiguous：最高分落在空平台/洞穴晶壁/UI 区域，不具备判别力；
  这只说明『现有夜世界阴性帧 + 这组家乡模板』不能互相验证，**不等于这批底图整体不可用**。
- 待取得无遮挡的家乡（home）真实帧后需复测：在该帧上 home_best 应显著高于夜世界帧才能放行。
- 视角/缩放: 模板为 3D 渲染原图，截图为设备实拍缩放，探针已做多尺度扫描。