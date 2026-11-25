# -*- coding: utf-8 -*-
"""审计 must-fix 八条离线自证（P0-01..P1-08）。

纯离线：不启窗、不联网、不发键、不碰模拟器/覆盖层。
运行：D:\\Python313\\python.exe tools\\audit_selfcheck.py
输出：out\\audit\\mustfix_selfcheck.txt（每条 PASS/FAIL + 关键数值）。

断言都是真检查：修复前对应条目会 FAIL，修复后才 PASS；不写恒 PASS。
"""
import ast
import json
import os
import re
import sys
import tempfile
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

RESULTS = []


def record(item, ok, detail=""):
    RESULTS.append((item, "PASS" if ok else "FAIL", detail))
    return ok


def read_text(rel):
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8") as f:
        return f.read()


# ---------------- P0-01：hud 线性公式 → Calib 单应（gold 55 栋数值证明） ----------------
def p001():
    from clashlab.geo import Calib

    gold_path = os.path.join(ROOT, "out", "snap", "gold", "home_village_gold.json")
    gold = json.load(open(gold_path, encoding="utf-8"))
    quad = gold["quad"]
    buildings = gold["buildings"]
    n = 44
    calib = Calib.from_quad(quad)
    q = np.array(quad, dtype=float)
    # 复刻改动前 hud.py:132-145 的老线性投影（cx/cy/kx/ky 四边线性插值）
    cx, cy = q[:, 0].mean(), q[:, 1].mean()
    kx = (q[1, 0] - q[3, 0]) / (2 * n)
    ky = (q[2, 1] - q[0, 1]) / (2 * n)

    errs_tile, errs_px, homo_rt = [], [], []
    for b in buildings:
        gx, gy = b["foot_tile_raw"]
        lpx = cx + (gx - gy) * kx
        lpy = cy + (gx + gy - n) * ky
        gpx, gpy = calib.tile_to_px(gx, gy)
        rx, ry = calib.px_to_tile(lpx, lpy)
        errs_tile.append(float(((rx - gx) ** 2 + (ry - gy) ** 2) ** 0.5))
        errs_px.append(float(((gpx - lpx) ** 2 + (gpy - lpy) ** 2) ** 0.5))
        # 单应往返 sanity：foot_px -> px_to_tile 应回到 foot_tile_raw
        px, py = b["foot_px"]
        hx, hy = calib.px_to_tile(px, py)
        homo_rt.append(float(((hx - gx) ** 2 + (hy - gy) ** 2) ** 0.5))

    et, ep, rt = np.array(errs_tile), np.array(errs_px), np.array(homo_rt)
    # 源码迁移断言：线性公式已删，改走 Calib
    hud_src = read_text(os.path.join("clashlab", "hud.py"))
    migrated = ("Calib.from_quad" in hud_src
                and "tile_to_px" in hud_src
                and "(gx - gy) * kx" not in hud_src
                and "已弃用：线性公式" in hud_src)
    ok = migrated and rt.max() < 0.5
    detail = (f"样本 {len(buildings)} 栋；旧线性 vs 单应：格误差 max={et.max():.3f} mean={et.mean():.3f}，"
              f"像素差 max={ep.max():.2f} mean={ep.mean():.2f}；单应往返 max={rt.max():.4f} 格；"
              f"源码迁移={migrated}")
    return record("P0-01", ok, detail)


# ---------------- P0-02：复核闸门尊重 [soft] ----------------
def p002():
    from clashlab import llm

    soft_only = [llm._soft("confidence 不在 0~1，已置空"),
                 llm._soft("entry_adjust 越界 50,50，已丢弃该条")]
    hard_mix = soft_only + [llm._hard("清洗后没有任何可用结论")]
    # 闸门逻辑（与 app.py:746 同款）：is_hard_rejection 才 rejected
    status_soft = "rejected" if llm.is_hard_rejection(soft_only) else "ok"
    status_hard = "rejected" if llm.is_hard_rejection(hard_mix) else "ok"
    src = read_text(os.path.join("clashlab", "app.py"))
    src_ok = ("llm.is_hard_rejection(issues)" in src
              and 'status = "ok" if not issues else "rejected"' not in src)
    ok = status_soft == "ok" and status_hard == "rejected" and src_ok
    return record("P0-02", ok,
                  f"soft-only 闸门={status_soft}（应 ok）；含 hard 闸门={status_hard}（应 rejected）；源码门控={src_ok}")


# ---------------- P0-03：live 不再硬编码 ----------------
def p003():
    import inspect
    from clashlab.farm import Farm

    src = read_text(os.path.join("clashlab", "app.py"))
    # 整文件断言：新写法 live=live 由配置驱动；旧硬编码调用形态已消失
    no_hardcode = "live=True, use_llm=True" not in src
    cfg_driven = 'self.cfg.get("farm_live"' in src and "live=live, use_llm=True" in src
    sig = inspect.signature(Farm.__init__)
    farm_default_live = sig.parameters["live"].default is False
    ok = no_hardcode and cfg_driven and farm_default_live
    return record("P0-03", ok,
                  f"_run_farm 无 live=True 硬编码={no_hardcode}；cfg 读取={cfg_driven}；"
                  f"Farm 默认 live=False={farm_default_live}")


# ---------------- P0-04：任意 CWD 锚定项目根 ----------------
def p004():
    from clashlab import paths

    cwd = os.getcwd()
    td = tempfile.mkdtemp(prefix="clashlab_cwd_probe_")
    try:
        os.chdir(td)  # 切到空目录，CWD 与项目根无关
        root = paths.project_root()
        resolved = paths.resolve_resource(os.path.join("layouts", "th13_sample.json"))
        root_ok = os.path.isfile(os.path.join(root, "clashlab", "geo.py"))
        file_ok = os.path.isfile(resolved)
        # 绝对路径原样透传
        abs_ok = paths.resolve_resource(os.path.join(ROOT, "clashlab", "geo.py")) == \
            os.path.join(ROOT, "clashlab", "geo.py")
        ok = root_ok and file_ok and abs_ok
        return record("P0-04", ok,
                      f"chdir 空目录后 root={root}（含 geo.py={root_ok}）；"
                      f"layouts/th13_sample.json 解析存在={file_ok}；绝对路径透传={abs_ok}")
    finally:
        os.chdir(cwd)
        try:
            os.rmdir(td)
        except OSError:
            pass


# ---------------- P0-05：空 content 结构化回退，不抛栈 ----------------
def p005():
    from clashlab import llm

    orig_post = llm._post
    orig_prov = llm.load_provider

    def fake_empty_post(url, key, payload, timeout=90):
        return {"choices": [{"message": {"content": ""}}]}

    llm._post = fake_empty_post
    llm.load_provider = lambda *a, **k: {"base": "http://127.0.0.1/x", "key": "fake",
                                        "timeout": 90, "source": "selftest"}
    try:
        res = llm.chat_robust([{"role": "user", "content": "x"}], max_tokens=10)
        no_raise = True
    except Exception as e:  # 必须不抛
        no_raise = False
        res = {"ok": False, "code": "RAISED", "attempts": 0, "last_reason": str(e)}
    finally:
        llm._post = orig_post
        llm.load_provider = orig_prov

    shape_ok = (not res["ok"] and res["code"] == "EMPTY_CONTENT"
                and res["attempts"] == 3 and bool(res["last_reason"])
                and {"ok", "code", "attempts", "last_reason", "stage"} <= set(res))
    # review_plan 全失败也不抛栈，返回四元组
    llm._post = fake_empty_post
    llm.load_provider = lambda *a, **k: {"base": "http://127.0.0.1/x", "key": "fake",
                                        "timeout": 90, "source": "selftest"}
    rp_raise = False
    rp = None
    try:
        rp = llm.review_plan("selftest_fake.json", {}, [], {}, ring_tiles=None, style="terse")
    except Exception:
        rp_raise = True
    finally:
        llm._post = orig_post
        llm.load_provider = orig_prov
    rp_ok = (not rp_raise and isinstance(rp, tuple) and len(rp) == 4
             and rp[0] is None and rp[3])
    ok = no_raise and shape_ok and rp_ok
    return record("P0-05", ok,
                  f"chat_robust ok={res.get('ok')} code={res.get('code')} "
                  f"attempts={res.get('attempts')} 形状完整={shape_ok}；"
                  f"review_plan 不抛={not rp_raise} 四元组={rp_ok}")


# ---------------- P0-06：缓存键带配置指纹，不串味 ----------------
def p006():
    from clashlab import prompts

    k1 = prompts._key("th13_sample.json", [], "terse",
                      extra_fp=prompts.fingerprint({"army": {"troops": "a"}}))
    k2 = prompts._key("th13_sample.json", [], "terse",
                      extra_fp=prompts.fingerprint({"army": {"troops": "b"}}))
    k1b = prompts._key("th13_sample.json", [], "terse",
                       extra_fp=prompts.fingerprint({"army": {"troops": "a"}}))
    differ = k1 != k2
    same = k1 == k1b
    # 旧键（无 fp）对两种 army 会撞键——新键必须不同
    old_a = prompts._key("th13_sample.json", [], "terse")
    old_b = prompts._key("th13_sample.json", [], "terse")
    old_collision = old_a == old_b
    src = read_text(os.path.join("clashlab", "prompts.py"))
    src_ok = "extra_fp" in src and "fingerprint" in src
    ok = differ and same and src_ok
    return record("P0-06", ok,
                  f"不同 army 键不同={differ}；同指纹键相同={same}；旧键撞键={old_collision}（已由指纹消除）；源码={src_ok}")


# ---------------- P1-01：退化四边形前置校验，返回 None 不抛 ----------------
def p101():
    from clashlab import vision

    # 2 点共线（点数不足）
    r1 = None
    try:
        r1 = vision.safe_calib([[0, 0], [10, 0]])
    except Exception:
        r1 = "RAISED"
    # 4 点共线
    r2 = None
    try:
        r2 = vision.safe_calib([[0, 0], [10, 0], [20, 0], [30, 0]])
    except Exception:
        r2 = "RAISED"
    # 合法菱形应给出 calib
    r3 = None
    try:
        r3 = vision.safe_calib([[520, 40], [1180, 360], [600, 730], [90, 360]])
    except Exception:
        r3 = "RAISED"
    ok = (r1 is None and r2 is None and r3 is not None
          and r1 != "RAISED" and r2 != "RAISED" and r3 != "RAISED")
    return record("P1-01", ok,
                  f"2点共线→{r1}；4点共线→{r2}；合法菱形→calib={'有' if r3 else '无'}；均未抛异常")


# ---------------- P1-08：密钥打码 + 残余扫描为 0 ----------------
def p108():
    from clashlab import llm

    # 测试 token 动态拼接，避免自检源码本身留下 sk- 明文样例
    fake_token = "sk-" + "v8Y8" + "ABCDEF1234567890xy"
    masked = llm.redact_secrets("token " + fake_token + " done")
    mask_ok = "sk-<redacted>" in masked and "v8Y8ABC" not in masked
    # 全仓残余扫描（跳过 dist / llm_cache / __pycache__ / 本自检脚本）
    pat = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
    skip = {"__pycache__", ".git", "llm_cache", "dist"}
    self_rel = os.path.relpath(__file__, ROOT)
    residual, hits = 0, []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d.lower() not in skip]
        for f in fn:
            ext = os.path.splitext(f)[1].lower()
            if ext not in {".py", ".json", ".md", ".txt", ".csv", ".log", ".ini",
                           ".cfg", ".toml", ".yaml", ".yml", ".html", ".js",
                           ".ps1", ".spec", ".bat", ".cmd", ".env"}:
                continue
            p = os.path.join(dp, f)
            if os.path.relpath(p, ROOT) == self_rel:
                continue
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            m = pat.findall(txt)
            if m:
                residual += len(m)
                hits.append(os.path.relpath(p, ROOT))
    log_src = read_text(os.path.join("out", "ui", "build_log.txt"))
    log_redacted = "<redacted>" in log_src and "sk-" not in re.sub(r"<redacted>", "", log_src)
    llm_export = hasattr(llm, "redact_secrets")
    ok = mask_ok and residual == 0 and log_redacted and llm_export
    return record("P1-08", ok,
                  f"打码={mask_ok}；全仓残余={residual} {hits if hits else ''}；"
                  f"build_log 已 redact={log_redacted}；llm.redact_secrets 导出={llm_export}")


# ---------------- 附加：改动文件语法可编译 ----------------
def compile_check():
    files = ["clashlab/hud.py", "clashlab/app.py", "clashlab/llm.py",
             "clashlab/vision.py", "clashlab/prompts.py", "clashlab/paths.py"]
    bad = []
    for rel in files:
        try:
            ast.parse(read_text(rel), filename=rel)
        except SyntaxError as e:
            bad.append(f"{rel}:{e.lineno}")
    ok = not bad
    return record("COMPILE", ok, f"AST 解析 {len(files)} 文件，失败={bad or '无'}")


def main():
    checks = [p001, p002, p003, p004, p005, p006, p101, p108, compile_check]
    for fn in checks:
        try:
            fn()
        except Exception as e:
            record(fn.__name__, False, f"自检自身异常：{e}\n{traceback.format_exc()[-400:]}")

    lines = ["ClashLab 审计 must-fix 八条离线自证", f"ROOT={ROOT}", ""]
    passed = 0
    for item, status, detail in RESULTS:
        if status == "PASS":
            passed += 1
        lines.append(f"[{status}] {item}  {detail}")
    lines.append("")
    lines.append(f"合计 {passed}/{len(RESULTS)} PASS")
    text = "\n".join(lines) + "\n"
    out_dir = os.path.join(ROOT, "out", "audit")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "mustfix_selfcheck.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print("written:", out_path)


if __name__ == "__main__":
    main()
