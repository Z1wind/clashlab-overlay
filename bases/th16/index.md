# TH16 阵型素材索引（采集批次）

采集时间：2026-11-23（UTC+8）。共 6 阵，均为 TH16；每阵 `base.png` 为实际下载的原始文件（未放大/未锐化/未风格化），`source.json` 记录来源与校验信息。

| 编号 | 站点 | 本数 | 角色标签 | 原始分辨率 | 完整性（完整/顶部裁切） | source_url | 取得时间 | 文件字节数 |
|---|---|---|---|---|---|---|---|---|
| 01 | clashofclans-layouts.com | TH16 | anti-3star, war-cwl | 2622x1206 | 完整 | https://www.clashofclans-layouts.com/plans/th_16/war_138.html | 2026-11-23T18:59:33+08:00 | 853705 |
| 02 | info-clash.com | TH16 | anti-air, anti-star-denial, war-cwl | 1000x460 | 完整（低分辨率，建议低可信度） | https://info-clash.com/layout/698e08085e456c11a24c68a9 | 2026-11-23T19:37:46+08:00 | 167665 |
| 03 | clashofclans-layouts.com | TH16 | war-cwl, square-grid（方阵/方格网格） | 2622x1206 | 完整 | https://www.clashofclans-layouts.com/plans/th_16/war_143.html | 2026-11-23T19:37:46+08:00 | 858441 |
| 04 | clashofclans-layouts.com | TH16 | anti-3star, war-cwl, ring-donut-core（环形/环核） | 2622x1206 | 顶部裁切 | https://www.clashofclans-layouts.com/plans/th_16/war_141.html | 2026-11-23T20:14:45+08:00 | 850008 |
| 05 | clashofclans-layouts.com | TH16 | anti-3star, war-cwl | 2622x1206 | 顶部裁切 | https://www.clashofclans-layouts.com/plans/th_16/war_139.html | 2026-11-23T20:14:45+08:00 | 840797 |
| 06 | clashofclans-layouts.com | TH16 | anti-2star, anti-everything, defence-trophy | 2622x1206 | 完整 | https://www.clashofclans-layouts.com/plans/th_16/defence_17.html | 2026-11-23T20:46:50+08:00 | 1069829 |

## 完整性说明（04/05 裁切，勿当完整图用）

- **04（war_141）顶部裁切**：村庄菱形上角（环带顶点）在画面外，顶部边缘约 2~3 栋小型建筑（小屋/加农炮类）贴边出画；底部与左右两侧完整。详见 `04/source.json` 的 `crop_note`。
- **05（war_139）顶部裁切**：村庄菱形上角在画面外，顶部边缘约 3~4 栋建筑（金/紫储金罐、加农炮类）贴边出画；底部与左右两侧完整。详见 `05/source.json` 的 `crop_note`。
- **06（defence_17）完整**：四边条带已逐边核验，菱形四角全部落在画面内，顶/底/左/右均有草地与森林留白，无贴边裁切。
- 01、03 原图完整；02 完整但仅 1000x460，单体偏小，建议低可信度。

## 角色覆盖与缺项说明

- anti-3star：✓（01、04、05，站点标题均明确 Anti 3 Stars CWL War Base；其中 04/05 顶部裁切）
- anti-air：✓（02，站点标题/标签明确 Anti-Air；但原图仅 1000x460、偏宽扁，标注精度差，建议降级为低可信度样本）
- anti-queen-charge / anti-blizzard（反女王穿云箭/反暴风雪）：✗ 未单独成阵。02 正文提及防空布置可牵制女王穿云箭，但页面未单独标注该角色，故不挂标签。
- 环形/环核阵（ring/donut-core）：✓（04，同心菱形环带包裹中央核心；顶部裁切，仅作环核形态参考）
- 方阵：✓（03，方格网格分格战争阵，完整）
- anti-2star / anti-everything：✓（06，完整全图）

## 采集说明

- 所有 source_url 均为本机实际访问过的页面；所有 base.png 均为从对应 image_url 实际下载成功的文件，字节数与分辨率已用 Pillow 逐张复核。
- 遵守各站 robots：clashofclans-layouts.com 无 Disallow；info-clash.com robots.txt 为 content-signal 声明、无禁止规则；均为逐页少量取用，未批量爬取，未碰登录墙/付费内容。
- 01/03/04/05/06 为 2622x1206 高分辨率全尺寸图；02 为 1000x460（长边达标但单体偏小，仅供参考）。
- 本机网络受限：Fandom/Reddit/blogger/oneclash 图床均不可达，bases-coc 图仅 720px 已淘汰；未启用自阵截屏备选。
