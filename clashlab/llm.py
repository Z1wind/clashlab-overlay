# -*- coding: utf-8 -*-
"""大模型接入层：直接复用本机 AstrBot 的 openai_1 provider（OpenAI 兼容）。

设计原则（与方案第 10 章一致）：
1. 模型不进实时回路：只做「离线的战术复核」「阵型标注」「样本解说」三种调用。
2. 模型输出一律当不可信输入：必须过 validate_* 校验器，越界/非法类型/数量异常直接拒绝，
   拒绝后不重试到底，而是回退到规则引擎的结论。
3. provider 走回退链：openai_2（首选，opencode zen）-> openai_1（旧 newapi，空返回已知）-> 全失败抛错。
   单次调用超时取配置；调用方（战术生成）另设总预算封顶，不把多次失败跑完。
4. 配置不写死在代码里：每次启动从 ~/.astrbot/data/cmd_config.json 的 provider_sources 读取，
   也支持环境变量 CLASHLAB_BASE / CLASHLAB_KEY / CLASHLAB_MODEL 覆盖（打包成 exe 后更稳）。
   key 绝不硬编码、绝不写日志；custom_headers（如 x-opencode-session / User-Agent）原样透传。
"""
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request

DEFAULT_PROVIDER = "openai_2"
# provider 回退顺序：openai_2 首选（opencode zen，需 custom_headers），openai_1 兜底（旧 newapi，
# 生产参数下 8/8 空返回，仅作占位尝试）；全部不可用由调用方走本地规则兜底。
PROVIDER_ORDER = ["openai_2", "openai_1"]
# 默认模型（两 provider 同名 model id；openai_1 实测空返回，靠 openai_2 拿到正文）。
DEFAULT_MODEL = "deepseek-v4.1-flash"
# 显式 model= 才用的长链；默认只走 DEFAULT_MODEL 快速档。
MODEL_CHAIN = [DEFAULT_MODEL]
VISION_MODEL = "deepseek-v4-flash-vision-exp"

# openai_2 缺失/无 headers 时的最小默认头（key 绝不写死，只补公共头）。
_DEFAULT_EXTRA_HEADERS = {
    "User-Agent": "astrbot-oc/1.0",
}

# P1-08：日志/落盘出口的密钥打码：sk- 开头的明文密钥一律替换为 sk-<redacted>
SK_KEY_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")


def redact_secrets(text):
    """打印/落盘前把 sk- 明文密钥替换为 sk-<redacted>；非字符串原样返回。"""
    if not isinstance(text, str):
        return text
    return SK_KEY_RE.sub("sk-<redacted>", text)


def _compact_messages(messages, char_cap=400):
    """精简 prompt：保留 system，user 内容截断到 char_cap 字（回退链第 3 步用）。"""
    out = []
    for m in messages or []:
        role = m.get("role", "user")
        content = m.get("content")
        if isinstance(content, list):
            # 多模态：只保留文本段并截断
            parts = [c.get("text", "") for c in content if isinstance(c, dict)
                     and c.get("type") == "text"]
            content = "\n".join(parts)
        content = str(content or "")
        out.append({"role": role, "content": content[:char_cap]})
    return out


def _classify_err(e):
    msg = str(e)
    if "空 content" in msg or "empty" in msg.lower():
        return "EMPTY_CONTENT"
    if "provider" in msg or "配置" in msg or "没有可用" in msg:
        return "NO_PROVIDER"
    return "NETWORK_OR_MODEL"


def chat_robust(messages, model=None, temperature=0.2, max_tokens=1200, timeout=None,
                provider=None, compact_messages=None, max_attempts=3):
    """带结构化回退链的 chat（P0-05），失败返回错误对象、绝不抛栈。

    阶段：
      1. original —— 原样调用；
      2. retry    —— 原样重试一次；
      3. compact_temp —— 精简 prompt + 降温(0.05)再试。
    成功：{"ok": True, "text", "model_used", "attempts", "stage"}；
    失败：{"ok": False, "code", "attempts", "last_reason", "stage", "text": "", "model_used": ""}。
    code ∈ {EMPTY_CONTENT, NO_PROVIDER, NETWORK_OR_MODEL, ALL_FAILED}。
    """
    stages = [
        ("original", messages, temperature),
        ("retry", messages, temperature),
        ("compact_temp", compact_messages or _compact_messages(messages), 0.05),
    ]
    attempts = 0
    last_reason, code, stage = "", "", ""
    for i, (stage, msgs, temp) in enumerate(stages[:max_attempts]):
        attempts = i + 1
        try:
            text, used = chat(msgs, model=model, temperature=temp,
                              max_tokens=max_tokens, timeout=timeout, provider=provider)
            return {"ok": True, "text": redact_secrets(text), "model_used": used,
                    "attempts": attempts, "code": "", "last_reason": "", "stage": stage}
        except Exception as e:  # 网络/额度/空 content/无 provider，记录后进入下一阶段
            last_reason = str(e)[:200]
            code = _classify_err(e)
            continue
    return {"ok": False, "code": code or "ALL_FAILED", "attempts": attempts,
            "last_reason": last_reason, "stage": stage, "text": "", "model_used": ""}

BUILDING_VOCAB = [
    "town-hall", "eagle-artillery", "monolith", "scattershot", "inferno-tower",
    "air-defense", "x-bow", "multi-archer-tower", "wizard-tower", "bomb-tower",
    "air-sweeper", "hidden-tesla", "spell-tower", "mortar", "archer-tower",
    "cannon", "firespitter", "wall",
]


def _astrbot_config_path():
    home = os.path.expanduser("~")
    return os.path.join(home, ".astrbot", "data", "cmd_config.json")


def _read_provider_cfg(name, cfg):
    """从 cmd_config.provider_sources 取指定 id 的一条；返回 None 表示没有。

    只回传 base/key/timeout/headers/model/source；key 不进任何日志（调用方负责 redact）。
    """
    for src in cfg.get("provider_sources", []):
        if src.get("id") != name:
            continue
        keys = src.get("key") or []
        key = keys[0] if isinstance(keys, list) and keys else (keys if isinstance(keys, str) else "")
        if not key:
            return None
        headers = dict(src.get("custom_headers") or {})
        # openai_2 的会话头缺失时补公共 User-Agent；业务会话头以配置文件为准，不伪造。
        headers.setdefault("User-Agent", _DEFAULT_EXTRA_HEADERS["User-Agent"])
        return {"base": (src.get("api_base") or "").rstrip("/"), "key": key,
                "timeout": float(src.get("timeout") or 90),
                "headers": headers,
                "model": src.get("model") or "",
                "source": "config:" + name}
    return None


def load_provider(name=None):
    """取一个可用 provider。name=None 按 PROVIDER_ORDER 顺序找第一个有 base+key 的。

    env 优先（CLASHLAB_BASE/KEY/TIMEOUT），env 不区分 provider，只用于打包 exe 兜底。
    返回 {"base","key","timeout","headers","model","source"}；取不到 base/key 即不可用，
    调用方按链继续找下一个，全部失败由上层走本地规则兜底。
    """
    env = os.environ
    if env.get("CLASHLAB_BASE") and env.get("CLASHLAB_KEY"):
        return {"base": env["CLASHLAB_BASE"].rstrip("/"), "key": env["CLASHLAB_KEY"],
                "timeout": float(env.get("CLASHLAB_TIMEOUT", 90)),
                "headers": dict(_DEFAULT_EXTRA_HEADERS), "model": "",
                "source": "env"}
    path = _astrbot_config_path()
    if not os.path.exists(path):
        return {"base": "", "key": "", "timeout": 90, "headers": {}, "model": "", "source": "missing"}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
    except Exception:
        return {"base": "", "key": "", "timeout": 90, "headers": {}, "model": "", "source": "unreadable"}
    names = [name] if name else PROVIDER_ORDER
    for n in names:
        prov = _read_provider_cfg(n, cfg)
        if prov and prov["base"] and prov["key"]:
            return prov
    return {"base": "", "key": "", "timeout": 90, "headers": {}, "model": "",
            "source": "no-provider:" + (name or ",".join(PROVIDER_ORDER))}


def available_models():
    """从 AstrBot 配置里列出 openai_1 下的模型 id（去掉 provider 前缀）。"""
    path = _astrbot_config_path()
    out = []
    if not os.path.exists(path):
        return out
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
    except Exception:
        return out
    for m in cfg.get("provider_settings", {}).get("models", []) or []:
        pass
    return out


def _post(url, key, payload, timeout=90, headers=None):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + key)
    for k, v in (headers or {}).items():
        if k.lower() in ("content-type", "authorization"):
            continue  # 基础头已设，不被配置覆盖
        req.add_header(str(k), str(v))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", "ignore")
    return json.loads(body)


def _build_payload(messages, model, temperature, max_tokens, reasoning_effort=None):
    """统一请求体组装（chat 与离线自证共用，避免两处漂移）。

    reasoning_effort：探测实测 openai_2 必须 "low" + max_tokens 3000 才不空；
    None 时不带该字段（视觉/分类等其他链路不受影响）。
    """
    payload = {"model": model, "messages": messages, "temperature": temperature,
               "max_tokens": max_tokens, "stream": False}
    if reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort
    return payload


def chat(messages, model=None, temperature=0.2, max_tokens=1200, timeout=None,
         provider=None, reasoning_effort=None):
    """最简 chat completions，provider 回退链 openai_2 -> openai_1。返回 (text, model_used)。

    provider 可传名字（openai_2/openai_1）或 provider dict；None 走默认顺序。
    任一 provider 空 content/网络异常/4xx5xx 都换下一个，全失败抛最后错误。
    reasoning_effort：传入（如 "low"）则写进请求体；默认 None 不带。
    """
    # provider 入参兼容：dict 直接用，str 按名加载，None 按顺序解析
    if isinstance(provider, dict) and provider.get("base"):
        chain_providers = [provider]
    elif provider:
        chain_providers = [load_provider(provider)]
    else:
        chain_providers = [load_provider(n) for n in PROVIDER_ORDER]
    last_err = None
    for prov in chain_providers:
        if not prov.get("base") or not prov.get("key"):
            last_err = RuntimeError(f"provider {prov.get('source', '?')} 无 base/key")
            continue
        chain = [model] if model else ([prov.get("model")] if prov.get("model") else list(MODEL_CHAIN))
        for m in chain:
            payload = _build_payload(messages, m, temperature, max_tokens,
                                     reasoning_effort=reasoning_effort)
            try:
                res = _post(prov["base"] + "/chat/completions", prov["key"], payload,
                            timeout=timeout or prov.get("timeout", 90),
                            headers=prov.get("headers"))
                choices = res.get("choices") or []
                if not choices:
                    last_err = RuntimeError("空返回")
                    continue
                msg = choices[0].get("message") or {}
                text = (msg.get("content") or "").strip()
                if not text:
                    last_err = RuntimeError("空 content")
                    continue
                return text, m
            except Exception as e:  # 网络/额度/模型不存在/401/403，换下一个 provider
                last_err = e
                continue
    raise RuntimeError(f"所有 provider 都失败：{last_err}")


def extract_json(text):
    """从模型输出里抠出第一个完整 JSON 对象（容忍 ```json 包裹和前后废话）。"""
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None


def chat_json(messages, model=None, retries=1, **kw):
    last = None
    for _ in range(retries + 1):
        text, used = chat(messages, model=model, **kw)
        obj = extract_json(text)
        if obj is not None:
            return obj, used, text
        last = text
    raise RuntimeError("模型没有返回可解析 JSON：" + (last or "")[:200])


# ---------------- 视觉通道 ----------------

def encode_image_jpeg(frame_or_path, max_width=1100, quality=82):
    import numpy as np
    import cv2
    if isinstance(frame_or_path, str):
        raw = np.fromfile(frame_or_path, dtype=np.uint8)
        img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    else:
        img = frame_or_path
    h, w = img.shape[:2]
    if w > max_width:
        scale = max_width / float(w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("图片编码失败")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def chat_vision(frame_or_path, prompt, model=VISION_MODEL, max_tokens=1600, timeout=None):
    b64 = encode_image_jpeg(frame_or_path)
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
        ],
    }]
    return chat(messages, model=model, max_tokens=max_tokens, temperature=0.1, timeout=timeout)


# ---------------- 校验器 ----------------

def _soft(msg):
    return "[soft] " + msg


def _hard(msg):
    return "[hard] " + msg


def is_hard_rejection(issues):
    """issues 里只要有 [hard] 条才算整条结论被拒；[soft] 只是丢弃局部条目的警告。"""
    return any(str(i).startswith("[hard]") for i in (issues or []))


def validate_tactics(obj, ring_tiles=None, max_entries=3):
    """校验战术复核输出，软/硬分离。

    硬拒绝（[hard]）：输出不是 JSON 对象、或清洗后没有任何可用结论（verdict/顺序/修正全空）。
    软警告（[soft]）：confidence 越界、某条 entry_adjust 坐标非法/越界/不在撒兵环——
    只丢弃该条 adjust，保留 verdict / strike_order / risks，整条结论不丢。
    返回 (清洗后对象, 问题列表)；调用方用 is_hard_rejection(issues) 决定是否整条拒收。
    """
    issues = []
    if not isinstance(obj, dict):
        return None, [_hard("输出不是 JSON 对象")]
    out = {"verdict": str(obj.get("verdict", ""))[:200],
           "confidence": obj.get("confidence"),
           "entry_adjust": [], "strike_order": [], "risks": [], "notes": ""}

    conf = out["confidence"]
    if not isinstance(conf, (int, float)) or not (0 <= float(conf) <= 1):
        issues.append(_soft("confidence 不在 0~1，已置空"))
        out["confidence"] = None

    ring = set((int(t[0]), int(t[1])) for t in ring_tiles) if ring_tiles else None
    for item in (obj.get("entry_adjust") or [])[:max_entries]:
        if not isinstance(item, dict):
            issues.append(_soft("entry_adjust 项不是对象，已跳过"))
            continue
        tile = item.get("tile")
        if not (isinstance(tile, list) and len(tile) == 2
                and all(isinstance(v, (int, float)) for v in tile)):
            issues.append(_soft(f"entry_adjust 坐标非法 {tile}，已丢弃该条"))
            continue
        tx, ty = int(round(tile[0])), int(round(tile[1]))
        if not (1 <= tx <= 43 and 1 <= ty <= 43):
            issues.append(_soft(f"entry_adjust 越界 {tx},{ty}，已丢弃该条"))
            continue
        if ring is not None and (tx, ty) not in ring:
            issues.append(_soft(f"entry_adjust 落在不可撒兵区 {tx},{ty}，已丢弃该条"))
            continue
        out["entry_adjust"].append({"id": str(item.get("id", ""))[:8],
                                    "tile": [tx, ty], "reason": str(item.get("reason", ""))[:120]})

    for it in (obj.get("strike_order") or [])[:8]:
        if isinstance(it, str) and it.strip():
            out["strike_order"].append(it.strip()[:40])

    for it in (obj.get("risks") or [])[:5]:
        if isinstance(it, str) and it.strip():
            out["risks"].append(it.strip()[:120])

    out["notes"] = str(obj.get("notes", ""))[:600]

    if not (out["verdict"] or out["strike_order"] or out["entry_adjust"] or out["risks"]):
        issues.append(_hard("清洗后没有任何可用结论（verdict/顺序/修正全空）"))
    return out, issues


def validate_layout(obj, min_buildings=6, max_buildings=70):
    """校验阵型标注输出：类型必须在词表内，坐标在 1..43。"""
    issues = []
    if not isinstance(obj, dict) or not isinstance(obj.get("buildings"), list):
        return [], ["缺少 buildings 数组"]
    seen = set()
    rows = []
    for b in obj["buildings"][:max_buildings + 20]:
        if not isinstance(b, dict):
            continue
        typ = str(b.get("type", "")).strip().lower()
        if typ not in BUILDING_VOCAB:
            issues.append(f"未知类型 {typ}")
            continue
        tile = b.get("tile")
        if not (isinstance(tile, list) and len(tile) == 2 and all(isinstance(v, (int, float)) for v in tile)):
            issues.append(f"坐标非法 {tile}")
            continue
        x, y = int(round(tile[0])), int(round(tile[1]))
        if not (1 <= x <= 43 and 1 <= y <= 43):
            issues.append(f"坐标越界 {x},{y}")
            continue
        key = (x, y)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"type": typ, "tile": [x, y], "level": int(b.get("level", 1) or 1),
                     "conf": float(b.get("conf", 0.5) or 0.5)})
    if len(rows) < min_buildings:
        issues.append(f"建筑数过少（{len(rows)}）")
    return rows, issues


# ---------------- 业务封装 ----------------

def review_plan(layout_name, report, plans, army, ring_tiles=None, style="terse",
                profile=None, prebattle=None):
    """让模型复核规则引擎给出的方案，返回 (复核结果, 模型名, 原始文本, 问题)。

    style: terse(默认,快) / coach / audit；提示词与上下文压缩全部走 prompts 层，
    本函数不复制提示词文本（避免两处漂移）。原位置参数签名保持向后兼容，style 只做可选 kw。

    P0-05：LLM 全失败（含空 content）不再抛栈，返回 (None, "", "", [软告警])，
    调用方应回退展示纯规则结果；错误细节在软告警文本里（code/attempts/last_reason）。
    P0-06：缓存键带 army/profile/prebattle 指纹，跨配置不串味。
    """
    from . import prompts
    fp = prompts.fingerprint({"army": army, "profile": profile, "prebattle": prebattle})
    cached = prompts.cache_get(layout_name, plans, style, extra_fp=fp)
    if cached:
        return (cached.get("clean"), cached.get("model_used", ""),
                cached.get("raw", ""), cached.get("issues", []))
    brief = prompts.compact_brief(layout_name, report, plans, army)
    msgs, st = prompts.build_review_messages(brief, style)
    # P0-05：原样 → 原样重试 → 精简降温，三段回退全失败返回结构化错误对象，不抛栈。
    res = chat_robust(msgs, max_tokens=st["max_tokens"], temperature=0.15,
                      compact_messages=_compact_messages(msgs))
    if not res["ok"]:
        issues = [f"[soft] LLM 不可用（{res['code']}，{res['attempts']} 次尝试，"
                  f"stage={res['stage']}）：{res['last_reason']}；当前为纯规则结果，未被模型否定"]
        return None, "", "", issues
    obj = extract_json(res["text"])
    if obj is None:
        return None, res["model_used"], res["text"], \
            ["[soft] 模型未返回可解析 JSON，当前为纯规则结果"]
    clean, issues = validate_tactics(obj, ring_tiles=ring_tiles)
    prompts.cache_put(layout_name, plans, style,
                      {"clean": clean, "model_used": res["model_used"], "raw": res["text"],
                       "issues": issues, "style": style},
                      extra_fp=fp)
    return clean, res["model_used"], res["text"], issues


def label_layout(frame, grid_hint="44x44"):
    """用视觉模型给侦察截图打阵型标签，返回 (buildings, 模型名, 问题, 原文)。"""
    prompt = (
        "这是一张《部落冲突》敌方阵型的侦察截图（俯视等距视角，网格 " + grid_hint + "，"
        "坐标原点在地图左上角，x 向右、y 向下）。\n"
        "请识别所有建筑，只输出 JSON：{\"buildings\":[{\"type\":\"\",\"tile\":[x,y],\"level\":1,\"conf\":0.8}]}\n"
        "type 只能取：" + "、".join(BUILDING_VOCAB) + "。\n"
        "tile 用 1~43 的整数格号；建筑看不清就给较低的 conf，不要编造。"
    )
    text, used = chat_vision(frame, prompt)
    obj = extract_json(text)
    buildings, issues = validate_layout(obj or {})
    return buildings, used, issues, text


# ---------------- CV 候选定位 + LLM 只判类型（P1 链路） ----------------

_CLASSIFY_PROMPT = (
    "这是《部落冲突》基地画面中一块被框出的候选区域（含少量周围背景）。\n"
    "只输出一个 JSON 对象：{\"present\": true或false, \"type\": \"建筑类型或none\", \"conf\": 0.0~1.0}\n"
    "type 只能取：{vocab}；若不是建筑或看不清，present=false、type=none。\n"
    "不要输出坐标，不要解释，不要 markdown，不要在 JSON 外写字。"
)


def classify_candidate_crop(crop, model=None, timeout=25, max_tokens=80):
    """对单块候选小图做类型判定：是不是建筑、是哪种。只判类型，不要求模型给坐标。

    返回 (info, used, elapsed, err)：info={present,type,conf}；失败时 info={}、err 非空。
    """
    import cv2
    ok, buf = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        return {}, "", 0.0, "裁剪图编码失败"
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    prompt = _CLASSIFY_PROMPT.replace("{vocab}", "、".join(BUILDING_VOCAB))
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}},
        ],
    }]
    t0 = time.time()
    try:
        text, used = chat(messages, model=model, max_tokens=max_tokens,
                          temperature=0.0, timeout=timeout)
    except Exception as e:
        return {}, "", round(time.time() - t0, 2), str(e)[:160]
    obj = extract_json(text) or {}
    info = {"present": bool(obj.get("present", False)),
            "type": str(obj.get("type", "")).strip().lower(),
            "conf": float(obj.get("conf", 0.5) or 0.5)}
    if info["type"] not in BUILDING_VOCAB:
        info["type"] = "none"
    return info, used, round(time.time() - t0, 2), ""


def judge_candidates(frame, calib, dets, max_calls=8, model=None, timeout=25,
                     match_tile_tol=1.5):
    """对 detect_structures 产出的候选逐个送模型判类型，就地回填 det['type']/['conf']/['source']。

    - 按候选面积降序取前 max_calls 送模型（成本控制，单图 ≤ max_calls 次调用）；
    - 模型若自报坐标，与候选中心偏差 > match_tile_tol 格则丢弃该次类型判定；
    - 调用失败不阻塞：该候选保留 source='cv_only'，错误进 stats['errors']。
    返回 (annotated_dets, stats, issues)。
    """
    t0 = time.time()
    stats = {"candidates_total": len(dets), "typed": 0, "cv_only": 0,
             "llm_calls": 0, "elapsed_s": 0.0, "model_used": "",
             "errors": [], "labels_source": "unavailable",
             "usable": False, "usable_reason": "", "confidence": 0.0}
    issues = []
    if not dets:
        stats["usable_reason"] = "CV 候选数为 0：未在标定区内发现建筑块"
        stats["labels_source"] = "no_candidates"
        return dets, stats, issues

    ordered = sorted(dets, key=lambda d: -d["area"])[:max_calls]
    used_models = []
    for det in ordered:
        x, y, w, h = det["box"]
        m = int(max(w, h) * 0.25)  # 上下文边距 25%
        x0 = max(0, x - m); y0 = max(0, y - m)
        x1 = min(frame.shape[1], x + w + m); y1 = min(frame.shape[0], y + h + m)
        crop = frame[y0:y1, x0:x1]
        if crop.size == 0:
            det["source"] = "cv_only"
            stats["cv_only"] += 1
            continue
        stats["llm_calls"] += 1
        info, used, _el, err = classify_candidate_crop(crop, model=model, timeout=timeout)
        if used:
            used_models.append(used)
        if err:
            stats["errors"].append(err)
            det["source"] = "cv_only"
            stats["cv_only"] += 1
            continue
        cand_tile = det["tile"]
        if info.get("tile"):  # 模型越界自报坐标时的防护（本提示词不要求给坐标）
            mx, my = info["tile"]
            dist = ((mx - cand_tile[0]) ** 2 + (my - cand_tile[1]) ** 2) ** 0.5
            if dist > match_tile_tol:
                issues.append(f"模型坐标偏离候选中心 {dist:.1f} 格（>{match_tile_tol}），丢弃类型判定")
                det["source"] = "cv_only"
                stats["cv_only"] += 1
                continue
        if info.get("present") and info.get("type") in BUILDING_VOCAB:
            det["type"] = info["type"]
            det["conf"] = round(float(info["conf"]), 3)
            det["source"] = "llm_crop"
            stats["typed"] += 1
        else:
            det["source"] = "cv_only"
            stats["cv_only"] += 1

    stats["model_used"] = used_models[0] if used_models else ""
    stats["elapsed_s"] = round(time.time() - t0, 2)
    stats["usable"] = stats["candidates_total"] > 0
    if stats["typed"] > 0:
        stats["labels_source"] = "llm_typed"
        stats["usable_reason"] = (f"标定成功，候选 {stats['candidates_total']} 个，"
                                  f"模型定型 {stats['typed']} 个（送判 {stats['llm_calls']} 个）")
    elif stats["llm_calls"] > 0 and not stats["errors"]:
        stats["labels_source"] = "cv_candidates_only"
        stats["usable_reason"] = "模型被调用但未给出可接受类型，仅保留 CV 候选"
    else:
        stats["labels_source"] = "llm_unavailable"
        stats["usable_reason"] = "模型不可用或调用全部失败，仅输出 CV 候选，不伪造类型"
    stats["confidence"] = round(stats["typed"] / max(stats["candidates_total"], 1), 3)
    return dets, stats, issues


def label_layout_from_candidates(frame, calib, grid_hint="44x44", max_calls=8,
                                 model=None, timeout=25, match_tile_tol=1.5):
    """CV 候选定位 + LLM 只判类型的完整封装。

    返回 (buildings, model_used, issues, extra, stats)：
    - buildings: 已定型 [{type, tile:[x,y], level, conf, source}]，未定型不进清单；
    - stats: 候选/定型/未匹配/调用次数/耗时/labels_source/usable/usable_reason 等可解释依据；
    整条链路失败时 buildings=[]、labels_source='llm_unavailable'，绝不塞假数据。
    """
    from . import vision
    dets = vision.detect_structures(frame, calib) if calib is not None else []
    dets, stats, issues = judge_candidates(
        frame, calib, dets, max_calls=max_calls, model=model,
        timeout=timeout, match_tile_tol=match_tile_tol)
    buildings = []
    for d in dets:
        if d.get("source") == "llm_crop" and d.get("type"):
            buildings.append({"type": d["type"],
                              "tile": [int(round(d["tile"][0])), int(round(d["tile"][1]))],
                              "level": 1, "conf": d.get("conf", 0.5),
                              "source": "llm_crop"})
    return buildings, stats["model_used"], issues, "", stats


def ping():
    """连通性自检：返回 (ok, 模型名, 耗时, 错误)"""
    t0 = time.time()
    try:
        text, used = chat([{"role": "user", "content": "只回复：pong"}], max_tokens=20)
        return True, used, round(time.time() - t0, 2), redact_secrets(text[:40])
    except Exception as e:
        return False, "", round(time.time() - t0, 2), redact_secrets(str(e)[:200])


if __name__ == "__main__":
    print(load_provider())
    print(ping())
