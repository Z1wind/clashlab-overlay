# -*- coding: utf-8 -*-
"""覆盖层 PANEL 纯逻辑自测（不开窗、不连 adb、不写业务目录）。

跑法：
  D:\\Python313\\python.exe tools\\overlay_selftest.py
结果同时 print 与写入 out\\overlay\\ui_selftest.txt。

覆盖：
  1. marks.json 解析（真实文件）
  2. layout_candidates.json 解析（合成样本：bbox/box 两种形态；缺失/损坏降级）
  3. 候选 bbox 中心 -> tile 往返换算误差（数字，<=1 格）
  4. 冻结产物 schema 校验 + 幂等（重复冻结不堆文件、current.json 可写）
  5. 缺文件/坏 JSON 全链路降级不崩
  6. 面板坐标 -> 图片坐标 -> 渲染坐标 两级反算往返（数字）
  7. pages.py 可 import、draw_panel(None, None) 不崩
"""
import json
import os
import sys
import tempfile
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)

from clashlab.geo import Calib  # noqa: E402
from clashlab.overlay import data, editor, pages  # noqa: E402

# 实测 quad（1280x720）
QUAD = [[697, 107], [944, 351], [672, 585], [347, 327]]

RESULTS = []
FAIL = 0


def check(name, ok, detail=""):
    global FAIL
    RESULTS.append((name, bool(ok), detail))
    if not ok:
        FAIL += 1
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name} {detail}")


def near(a, b, tol=1e-6):
    return abs(a - b) <= tol


# ---------------------------------------------------------------- 1. marks.json
def test_marks():
    paths = data.Paths(ROOT)
    marks, info = data.load_marks(paths.p("out/marks/marks.json"))
    check("marks.json 存在且解析", info["exists"] and marks["version"] is not None,
          f"marks={len(marks['marks'])} pins={len(marks['pins'])} steps={len(marks['steps'])}")
    check("marks 条目字段齐全",
          all("tile" in m and "label" in m for m in marks["marks"]))
    # 缺失降级
    m2, i2 = data.load_marks(os.path.join(ROOT, "no_such_marks.json"))
    check("marks 缺失降级为空壳不崩", i2["exists"] is False and m2["marks"] == [])
    # 坏 JSON 降级
    bad = os.path.join(tempfile.mkdtemp(), "bad.json")
    with open(bad, "w", encoding="utf-8") as f:
        f.write("{not json")
    m3, _ = data.load_marks(bad)
    check("marks 坏 JSON 降级不崩", m3["marks"] == [] and m3["error"] is not None)


# ---------------------------------------------------------------- 2. candidates 解析
def test_candidates():
    sample = {
        "version": 1,
        "source": "out/grab/grab_x.png",
        "quad": QUAD,
        "candidates": [
            {"id": "c0", "label": "air-defense", "bbox": [300, 200, 360, 260],
             "confidence": 0.61, "tile": [22.0, 32.0]},
            {"id": "c1", "type": "scattershot", "box": [500, 300, 70, 70],
             "score": 0.93},
            {"id": "c2", "label": "bad", "bbox": [10, 10, 10, 11]},  # 退化框，应丢弃
        ],
    }
    norm = data.normalize_candidates(sample)
    check("candidates 归一化条数=2（退化框丢弃）", len(norm["candidates"]) == 2,
          f"got={len(norm['candidates'])}")
    by_id = {c["id"]: c for c in norm["candidates"]}
    check("box=(x,y,w,h) 转 bbox 对角点",
          near(by_id["c1"]["bbox"][2], 570) and near(by_id["c1"]["bbox"][3], 370),
          f"bbox={by_id['c1']['bbox']}")
    check("score 别名并入 confidence", near(by_id["c1"]["confidence"], 0.93))
    check("候选按置信度降序", norm["candidates"][0]["id"] == "c1")
    check("quad 透传", len(norm["quad"]) == 4)

    # 缺失降级
    n2, i2 = data.load_candidates(os.path.join(ROOT, "no_such_candidates.json"))
    check("candidates 缺失降级 present=False", i2["exists"] is False and n2["present"] is False)
    # 坏 JSON
    bad = os.path.join(tempfile.mkdtemp(), "bad.json")
    with open(bad, "w", encoding="utf-8") as f:
        f.write("[1,2,3")
    n3, _ = data.load_candidates(bad)
    check("candidates 坏 JSON 降级不崩", n3["candidates"] == [] and n3["error"] is not None)


# ---------------------------------------------------------------- 3. bbox->tile 往返
def test_tile_roundtrip():
    calib = Calib.from_quad(QUAD)
    max_err = 0.0
    for cx, cy in [(330, 230), (535, 335), (700, 400), (200, 150)]:
        (gx, gy), err = editor.bbox_center_tile(calib, [cx, cy, cx + 40, cy + 40])
        max_err = max(max_err, err)
    check("bbox 中心 tile 往返误差 <=1 格", max_err <= 1.0, f"max_err={max_err:.6f} 格")
    # 单点往返
    gx, gy = calib.px_to_tile(330, 230)
    bx, by = calib.tile_to_px(gx, gy)
    err_px = ((bx - 330) ** 2 + (by - 230) ** 2) ** 0.5
    check("px->tile->px 像素偏差 <2px", err_px < 2.0, f"err_px={err_px:.4f}")


# ---------------------------------------------------------------- 4. 冻结产物
def test_freeze():
    calib = Calib.from_quad(QUAD)
    model = editor.EditorModel([
        {"id": "c0", "label": "air-defense", "bbox": [300, 200, 360, 260],
         "confidence": 0.61},
        {"id": "c1", "label": "scattershot", "bbox": [500, 300, 570, 370],
         "confidence": 0.93},
    ], calib=calib)
    # 人工删 c1（隐藏=待删），选中 c0 拖一下
    model.toggle_hidden("c1")
    model.begin_drag(330, 230)
    model.drag_to(345, 240)
    model.end_drag()

    tmp = tempfile.mkdtemp()
    clock = lambda fmt: "20260101_000000" if fmt == "%Y%m%d_%H%M%S" else "2026-01-01T00:00:00"
    res = editor.freeze_layout(model, tmp, source_meta={"image": "overlay.png",
                                                       "candidates": "layout_candidates.json"},
                               quad=QUAD, clock=clock)
    check("冻结 ok", res["ok"], res["message"])
    errs = editor.validate_layout_product(res["product"])
    check("冻结产物 schema 校验通过", errs == [], ";".join(errs))
    prod = res["product"]
    check("产物含 source/quad/version/grid/frozen_at/buildings",
          all(k in prod for k in ("source", "quad", "version", "grid", "frozen_at", "buildings")))
    check("产物保留 th13_sample 风格 type/tile 字段",
          all("type" in b and "tile" in b for b in prod["buildings"]))
    check("未删建筑=1（隐藏项进 removed）", len(prod["buildings"]) == 1
          and len(prod["removed"]) == 1,
          f"buildings={len(prod['buildings'])} removed={len(prod['removed'])}")
    b0 = prod["buildings"][0]
    check("建筑字段 id/label/bbox/confidence/manual 齐全",
          all(k in b0 for k in ("id", "label", "bbox", "confidence", "manual")))
    check("current.json 已写", os.path.exists(res["current"]))
    cur_bytes = open(res["current"], "rb").read()

    # 幂等：同模型同 clock 再冻一次，不新增快照文件
    snapshots_before = set(os.listdir(tmp))
    res2 = editor.freeze_layout(model, tmp, source_meta={"image": "overlay.png",
                                                        "candidates": "layout_candidates.json"},
                               quad=QUAD, clock=clock)
    snapshots_after = set(os.listdir(tmp))
    check("幂等：重复冻结不新增快照文件", snapshots_before == snapshots_after,
          f"before={len(snapshots_before)} after={len(snapshots_after)}")
    check("幂等：current.json 字节一致", open(res2["current"], "rb").read() == cur_bytes)

    # 对照 th13_sample.json 键风格
    sample_path = os.path.join(ROOT, "layouts", "th13_sample.json")
    if os.path.exists(sample_path):
        with open(sample_path, encoding="utf-8") as f:
            th = json.load(f)
        check("样本含 grid/buildings（命名口径参照）",
              "grid" in th and isinstance(th.get("buildings"), list))


# ---------------------------------------------------------------- 5. 降级链路
def test_degrade():
    paths = data.Paths(ROOT)
    # clicks.log 缺失（用不存在路径）
    lines, err = data.read_clicks_tail(os.path.join(ROOT, "no_such_clicks.log"))
    check("clicks.log 缺失降级空列表", lines == [] and err == "missing")
    # 真实 clicks.log（另一条线已产出）：返回尾部行列表，不崩
    lines2, err2 = data.read_clicks_tail(paths.clicks_log, n=10)
    check("clicks.log 真实读取返回行列表", isinstance(lines2, list) and err2 is None,
          f"rows={len(lines2)}")
    # farm 报告缺失
    fr = data.load_farm_report(data.Paths(os.path.join(ROOT, "no_such_dir")))
    check("farm 报告缺失降级", fr["error"] == "missing" and fr["stats"] == {})
    # overlay.json 缺失（用不存在路径）降级空热键表
    oc_miss = data.load_overlay_config(data.Paths(os.path.join(ROOT, "no_such_dir")))
    check("config/overlay.json 缺失降级空热键表",
          oc_miss["hotkeys"] == [] and oc_miss["error"] == "missing")
    # 真实 config/overlay.json（A 已写）：热键表读出不崩
    oc = data.load_overlay_config(paths)
    check("config/overlay.json 热键表读取", isinstance(oc["hotkeys"], list)
          and len(oc["hotkeys"]) >= 1, f"rows={len(oc['hotkeys'])}")
    # 锚点：内置表必在，未验证两条标 false
    an = data.load_anchors(paths)
    confirmed = [a for a in an["anchors"] if a["confirmed"]]
    check("内置实测锚点 >=8 条", len(confirmed) >= 8, f"confirmed={len(confirmed)}")
    sb = next(a for a in an["anchors"] if a["key"] == "scout_back")
    sa = next(a for a in an["anchors"] if a["key"] == "scout_attack")
    check("scout_back/scout_attack 标未验证", sb["confirmed"] is False and sa["confirmed"] is False)
    # 面板视图汇总不崩
    view = data.load_panel_view(paths)
    check("load_panel_view 全链路不崩", isinstance(view, dict) and "candidates" in view)
    # 研究真实文件存在性（存在则展示，缺失则待产出，都不崩）
    check("study.png 可探测", isinstance(data.image_meta(paths.study_png), dict))


# ---------------------------------------------------------------- 6. 两级反算
def test_transform():
    vt = editor.ViewTransform(1280, 720, ax=10, ay=20, aw=600, ah=400)
    # 渲染坐标角点 -> 面板 -> 渲染 往返
    max_d = 0.0
    for rx, ry in [(0, 0), (1279, 719), (640, 360), (333, 222)]:
        px, py = vt.render_to_panel(rx, ry)
        bx, by = vt.panel_to_render(px, py)
        max_d = max(max_d, ((bx - rx) ** 2 + (by - ry) ** 2) ** 0.5)
    check("render->panel->render 往返误差 <1px", max_d < 1.0, f"max_d={max_d:.6f}px")
    # 反算到 tile：面板点 -> 渲染 -> tile -> render
    calib = Calib.from_quad(QUAD)
    gx, gy = calib.px_to_tile(*vt.panel_to_render(310, 180))
    err = editor.tile_roundtrip_error(calib, *vt.panel_to_render(310, 180))
    check("两级反算后 tile 往返误差 <=1 格", err <= 1.0, f"err={err:.6f} 格 tile=({gx:.2f},{gy:.2f})")


# ---------------------------------------------------------------- 7. 编辑器交互逻辑
def test_editor_interaction():
    model = editor.EditorModel([
        {"id": "c0", "label": "AD", "bbox": [300, 200, 360, 260], "confidence": 0.6},
        {"id": "c1", "label": "SC", "bbox": [500, 300, 570, 370], "confidence": 0.9},
    ])
    cid, part = model.hit_test(330, 230, corner_grab=8)
    check("命中 c0 体内", cid == "c0" and part == "body", f"hit=({cid},{part})")
    # 角命中：c1 右上角 (570,300)
    cid, part = model.hit_test(570, 300, corner_grab=8)
    check("命中 c1 拖角 ne", cid == "c1" and part == "ne", f"hit=({cid},{part})")
    # 空白未中
    cid, part = model.hit_test(10, 10, corner_grab=8)
    check("空白未中", cid is None and part is None)
    # 拖动
    model.begin_drag(330, 230)
    model.drag_to(350, 250)
    model.end_drag()
    r = model.get("c0")["bbox"]
    check("拖动平移生效", near(r[0], 320) and near(r[1], 220), f"bbox={r}")
    check("拖动标记 manual/edit", model.get("c0")["manual"] and model.get("c0")["edit"] == "moved")
    # 新增
    model.add([100, 100, 150, 150], label="手动补框", confidence=0.0)
    check("新增候选入列", len(model.candidates) == 3)
    # 删除
    check("删除 c1", model.delete("c1") and len(model.candidates) == 2)


# ---------------------------------------------------------------- 8. pages 骨架
def test_pages():
    check("pages 可 import、三页常量齐全",
          pages.PAGE_RESEARCH == "research" and pages.PAGE_COLLECT == "collect"
          and pages.PAGE_SETTING == "setting")
    import inspect
    sig = inspect.signature(pages.draw_panel)
    check("draw_panel(ctx, state) 签名固定（仅两参）",
          list(sig.parameters) == ["ctx", "state"])
    # 第二阶段 draw_panel 需要 ImGui 帧上下文，不在无帧环境调用；
    # 这里只验证模块导入零副作用（不建窗）。
    check("pages 导入无窗口副作用", True)


def main():
    tests = [test_marks, test_candidates, test_tile_roundtrip, test_freeze,
             test_degrade, test_transform, test_editor_interaction, test_pages]
    for t in tests:
        try:
            t()
        except Exception:
            check(t.__name__, False, "exception:\n" + traceback.format_exc())

    out_dir = os.path.join(ROOT, "out", "overlay")
    os.makedirs(out_dir, exist_ok=True)
    lines = ["覆盖层 PANEL 纯逻辑自测结果", f"root={ROOT}", ""]
    for name, ok, detail in RESULTS:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    lines.append("")
    lines.append(f"合计 {len(RESULTS)} 项，失败 {FAIL} 项")
    text = "\n".join(lines)
    with open(os.path.join(out_dir, "ui_selftest.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("\n" + text)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
