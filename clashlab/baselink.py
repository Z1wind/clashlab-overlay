# -*- coding: utf-8 -*-
"""Clash of Clans 阵型分享链接解析器（link.clashofclans.com OpenLayout）。

参考来源（MIT 兼容）
--------------------
* Peter537/clash-of-clans-base-validator（MIT License）—— docs/sources.md 第 43-47 节
  明确记录：官方分享链接形如
  https://link.clashofclans.com/<language>?action=OpenLayout&id=TH<lv>:<HV|WB>:<payload>，
  且 payload 被当作 opaque，社区尚未建立「坐标 <-> 链接」的 codec。
  本仓库 vendored 副本：out/overlay/_p3a/upstream/clash-of-clans-base-validator-main。
* 本项目 bases/th16/{01,03,04,05,06}/source.json 中保存的 5 条真实 copy_link
  （2026-11-23 从 clashofclans-layouts.com 抓取）。

本模块的实测结论（可复跑：tools/baselink_probe.py --bases-dir bases/th16）
-----------------------------------------------------------------------------
5 条真实链接的 payload 都是 32 个 base64url 字符 -> 24 字节：

    00 00 00 10 | 00 00 00 02 | <16 字节不透明值>
    +- u32 BE -+ +- u32 BE -+

前 8 字节在 5 条样本（TH16 / WB x4 + HV x1）中逐字节一致，后 16 字节随机。
24 字节无法容纳一个 44x44、100+ 建筑的阵型（即使压缩也远不够），
且 link.clashofclans.com 落地页只含 clashofclans:// 深链、不含任何 tile 数据
（实测页面中 OpenLayout 命中 0 次、payload 子串命中 0 次）。
因此结论是：链接 id 是不透明引用（大概率由游戏服务器解析），离线无法还原建筑坐标。

本模块因此提供三层能力
----------------------
1. 严格解析/诊断：parse_link / parse_id / decode_payload / parse_envelope；
2. 可插拔 codec 链（zlib/gzip/bz2/lzma/brotli/raw-deflate + JSON 布局 + 合成 COCL 二进制），
   真实格式一旦公开，注册新 codec 即可；
3. schema 适配：to_layout_json 输出与 bases/th16/*/layout.json 完全相同的 schema
   （name / grid / note / buildings / walls）。

诚实声明
--------
COCL 二进制格式是本模块自定义的合成格式，仅用于测试解码管线，不是 Supercell 的
真实格式；真实链接不会命中它（magic 校验失败）。
"""
from __future__ import annotations

import base64
import binascii
import bz2
import gzip
import json
import lzma
import re
import struct
import zlib
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlsplit

__all__ = [
    "BaseLinkError",
    "LayoutDecodeError",
    "BaseLink",
    "PayloadEnvelope",
    "DecodedLayout",
    "CodecAttempt",
    "LayoutDecodeResult",
    "parse_link",
    "parse_id",
    "decode_payload",
    "parse_envelope",
    "classify_payload",
    "decode_layout_payload",
    "to_layout_json",
    "undecodable_layout",
    "build_layout_from_link",
    "analyze_link",
    "encode_cocl_layout",
    "SYNTHETIC_BUILDING_TYPES",
    "GRID_SIZE",
    "LINK_HOST",
]

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

LINK_SCHEME = "https"
LINK_HOST = "link.clashofclans.com"
OPEN_ACTION = "OpenLayout"

GRID_SIZE = 44  # 官方阵型板 44x44，坐标 0..43

#: 语言路径：/en、/en-US（官方分享链接带语言段）
_LANGUAGE_PATH_RE = re.compile(r"^/[a-z]{2}(?:-[A-Za-z]{2})?$")

#: id 参数：TH<level>:<HV|WB>:<base64url payload>
_ID_RE = re.compile(r"^TH(?P<th>[1-9][0-9]*):(?P<village>HV|WB):(?P<payload>[A-Za-z0-9_-]+)$")

#: payload 字符集（base64url，无填充）
_PAYLOAD_RE = re.compile(r"^[A-Za-z0-9_-]+$")

VILLAGE_NAMES: Dict[str, str] = {"HV": "home-village", "WB": "war-base"}

#: 真实样本里出现的 24 字节信封：u32 BE 声明长度 16 + u32 BE kind 2 + 16 字节值
OPAQUE_TOKEN_LEN = 24
OPAQUE_TOKEN_DECLARED_LENGTH = 16
OPAQUE_TOKEN_KINDS = (1, 2)

#: 合成 COCL 二进制格式（本模块自定义，仅供测试/管线验证）
COCL_MAGIC = b"COCL"
COCL_VERSION = 1
COCL_HEADER_SIZE = 10  # magic4 + version1 + grid1 + n_build2 + n_wall2

#: 合成格式的 type id -> layout.json 里的 type 名（占位映射，真实 id 未知）
SYNTHETIC_BUILDING_TYPES: Dict[int, str] = {
    1: "town-hall",
    2: "clan-castle",
    3: "eagle-artillery",
    4: "monolith",
    5: "scattershot",
    6: "spell-tower",
    7: "inferno-tower",
    8: "x-bow",
    9: "air-defense",
    10: "air-sweeper",
    11: "wizard-tower",
    12: "archer-tower",
    13: "cannon",
    14: "mortar",
    15: "bomb-tower",
    16: "hidden-tesla",
    17: "ricochet-cannon",
    18: "firespitter",
}
_SYNTHETIC_TYPE_IDS: Dict[str, int] = {v: k for k, v in SYNTHETIC_BUILDING_TYPES.items()}

#: layout.json 的合法建筑类型（与 bases/th16 现有数据一致）
KNOWN_LAYOUT_TYPES = tuple(sorted(SYNTHETIC_BUILDING_TYPES.values()))

# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------


class BaseLinkError(ValueError):
    """分享链接格式错误。code 是稳定的机器可读错误码。"""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__("[%s] %s" % (code, message))


class LayoutDecodeError(ValueError):
    """payload 无法按已知 codec 还原成阵型。"""


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaseLink:
    """一条已校验的 OpenLayout 分享链接。"""

    url: str
    town_hall: int
    village: str  # "HV" | "WB"
    payload: str
    language: str = ""

    @property
    def village_name(self) -> str:
        return VILLAGE_NAMES[self.village]

    def to_dict(self) -> Dict[str, object]:
        return {
            "url": self.url,
            "town_hall": self.town_hall,
            "village": self.village,
            "village_name": self.village_name,
            "payload": self.payload,
            "language": self.language,
        }


@dataclass(frozen=True)
class PayloadEnvelope:
    """payload 字节的头部结构（真实样本实测为 u32 BE length + u32 BE kind + value）。"""

    raw: bytes
    declared_length: Optional[int]
    kind: Optional[int]
    value: bytes

    @property
    def consistent(self) -> bool:
        return self.declared_length is None or self.declared_length == len(self.value)

    def to_dict(self) -> Dict[str, object]:
        return {
            "raw_len": len(self.raw),
            "declared_length": self.declared_length,
            "kind": self.kind,
            "value_len": len(self.value),
            "value_hex": self.value.hex(),
            "consistent": self.consistent,
        }


@dataclass(frozen=True)
class DecodedLayout:
    """已还原的阵型：buildings=(type, x, y)，walls=(x, y)，坐标均为左上角 tile。"""

    buildings: Tuple[Tuple[str, int, int], ...]
    walls: Tuple[Tuple[int, int], ...]
    codec: str
    grid: int = GRID_SIZE


@dataclass(frozen=True)
class CodecAttempt:
    """一次 codec 尝试的结果（无论成败都记录，便于诊断）。"""

    codec: str
    ok: bool
    detail: str

    def to_dict(self) -> Dict[str, object]:
        return {"codec": self.codec, "ok": self.ok, "detail": self.detail}


@dataclass(frozen=True)
class LayoutDecodeResult:
    """payload -> 阵型的完整解码结果。"""

    ok: bool
    codec: Optional[str]
    layout: Optional[DecodedLayout]
    attempts: Tuple[CodecAttempt, ...]
    payload_kind: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "codec": self.codec,
            "payload_kind": self.payload_kind,
            "attempts": [a.to_dict() for a in self.attempts],
        }


# ---------------------------------------------------------------------------
# 链接解析
# ---------------------------------------------------------------------------


def parse_id(ident: str, url: str = "") -> BaseLink:
    """解析 TH<lv>:<HV|WB>:<payload> 形式的 id 字符串。"""
    if not isinstance(ident, str) or not ident:
        raise BaseLinkError("empty_id", "id 不能为空")
    match = _ID_RE.fullmatch(ident.strip())
    if match is None:
        raise BaseLinkError(
            "bad_id",
            "id 必须形如 TH<number>:HV|WB:<base64url>，实际为 %r" % (ident[:80],),
        )
    return BaseLink(
        url=url,
        town_hall=int(match.group("th")),
        village=match.group("village"),
        payload=match.group("payload"),
    )


def parse_link(url: str) -> BaseLink:
    """严格解析并校验一条 link.clashofclans.com OpenLayout 分享链接。

    规则与上游 MIT 校验器（coc_base/validate.py:15-29）一致：
    HTTPS、固定 host、语言路径（/en 或 /en-US，也接受无语言段）、
    查询串恰好 action=OpenLayout 与单个 id。
    """
    if not isinstance(url, str) or not url.strip():
        raise BaseLinkError("empty_url", "链接不能为空")
    text = url.strip()
    parsed = urlsplit(text)
    if parsed.scheme.lower() != LINK_SCHEME:
        raise BaseLinkError("bad_scheme", "必须是 https 链接，实际 %r" % parsed.scheme)
    if parsed.netloc.lower() != LINK_HOST:
        raise BaseLinkError("bad_host", "host 必须是 %s，实际 %r" % (LINK_HOST, parsed.netloc))
    if parsed.fragment:
        raise BaseLinkError("bad_fragment", "分享链接不应带 fragment")
    path = parsed.path
    if path not in ("", "/") and _LANGUAGE_PATH_RE.fullmatch(path) is None:
        raise BaseLinkError("bad_path", "路径应为语言段 /en 或 /en-US，实际 %r" % path)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if set(query) != {"action", "id"}:
        raise BaseLinkError("bad_query", "查询串必须恰好是 action 与 id，实际 %r" % sorted(query))
    if query["action"] != [OPEN_ACTION]:
        raise BaseLinkError("bad_action", "action 必须是 %s" % OPEN_ACTION)
    if len(query["id"]) != 1:
        raise BaseLinkError("bad_query", "id 必须恰好出现一次")
    link = parse_id(query["id"][0], url=text)
    return BaseLink(
        url=link.url,
        town_hall=link.town_hall,
        village=link.village,
        payload=link.payload,
        language=path.strip("/"),
    )


def decode_payload(payload: str) -> bytes:
    """把 base64url payload 解成字节（容忍尾部 = 填充，自动补齐）。"""
    if not isinstance(payload, str) or not payload:
        raise BaseLinkError("empty_payload", "payload 不能为空")
    stripped = payload.rstrip("=")
    if stripped == "" or "=" in stripped:
        raise BaseLinkError("bad_payload_chars", "payload 只允许 base64url 字符 [A-Za-z0-9_-] 与尾部填充")
    if _PAYLOAD_RE.fullmatch(stripped) is None:
        raise BaseLinkError("bad_payload_chars", "payload 只允许 base64url 字符 [A-Za-z0-9_-]")
    padded = stripped + "=" * (-len(stripped) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii"))
    except (binascii.Error, ValueError) as exc:
        raise BaseLinkError("bad_payload_base64", "payload 不是合法 base64url：%s" % exc)


def parse_envelope(raw: bytes) -> PayloadEnvelope:
    """解析 payload 字节的头部信封；不足 8 字节时 declared_length/kind 为 None。"""
    if len(raw) >= 8:
        declared = int.from_bytes(raw[0:4], "big")
        kind = int.from_bytes(raw[4:8], "big")
        return PayloadEnvelope(raw=raw, declared_length=declared, kind=kind, value=raw[8:])
    return PayloadEnvelope(raw=raw, declared_length=None, kind=None, value=raw)


def classify_payload(raw: bytes) -> str:
    """给 payload 字节分类：真实不透明 token / 合成格式 / 压缩候选 / 未知。"""
    if raw.startswith(COCL_MAGIC):
        return "cocl-synthetic"
    if (
        len(raw) == OPAQUE_TOKEN_LEN
        and int.from_bytes(raw[0:4], "big") == OPAQUE_TOKEN_DECLARED_LENGTH
        and len(raw[8:]) == OPAQUE_TOKEN_DECLARED_LENGTH
    ):
        return "opaque-token-v1"
    if raw[:2] in (b"\x78\x9c", b"\x78\xda", b"\x78\x01") or raw.startswith(
        (b"\x1f\x8b", b"BZh", b"\xfd7zXZ\x00")
    ):
        return "compressed-candidate"
    return "unknown"


# ---------------------------------------------------------------------------
# 合成 COCL 格式（仅测试/管线验证）
# ---------------------------------------------------------------------------


def encode_cocl_layout(
    buildings: Iterable[Sequence[object]], walls: Iterable[Sequence[int]] = ()
) -> bytes:
    """把 (type, x, y) 列表编码成未压缩的 COCL v1 二进制块。

    布局::

        magic 4s = b"COCL" | version u8 = 1 | grid u8 = 44
        n_buildings u16 LE | n_walls u16 LE
        buildings: n x (type_id u8, x u8, y u8)
        walls:     n x (x u8, y u8)

    这是本模块自定义的合成格式，不是 Supercell 真实格式，仅用于覆盖解码管线。
    """
    rows: List[Tuple[int, int, int]] = []
    for item in buildings:
        if len(item) != 3:
            raise LayoutDecodeError("building 必须是 (type, x, y)，实际 %r" % (item,))
        type_name, x, y = item
        if type_name not in _SYNTHETIC_TYPE_IDS:
            raise LayoutDecodeError("未知合成 type：%r" % (type_name,))
        x, y = int(x), int(y)
        if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
            raise LayoutDecodeError("tile 越界：(%d, %d)" % (x, y))
        rows.append((_SYNTHETIC_TYPE_IDS[type_name], x, y))
    wall_rows: List[Tuple[int, int]] = []
    for item in walls:
        if len(item) != 2:
            raise LayoutDecodeError("wall 必须是 (x, y)，实际 %r" % (item,))
        x, y = int(item[0]), int(item[1])
        if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
            raise LayoutDecodeError("wall tile 越界：(%d, %d)" % (x, y))
        wall_rows.append((x, y))
    head = struct.pack("<4sBBHH", COCL_MAGIC, COCL_VERSION, GRID_SIZE, len(rows), len(wall_rows))
    body = bytearray(head)
    for tid, x, y in rows:
        body.extend((tid, x, y))
    for x, y in wall_rows:
        body.extend((x, y))
    return bytes(body)


def _layout_from_cocl(blob: bytes) -> DecodedLayout:
    if not blob.startswith(COCL_MAGIC):
        raise LayoutDecodeError("magic 不是 COCL")
    if len(blob) < COCL_HEADER_SIZE:
        raise LayoutDecodeError("COCL 头不足 %d 字节" % COCL_HEADER_SIZE)
    version, grid, n_build, n_wall = struct.unpack_from("<BBHH", blob, 4)
    if version != COCL_VERSION:
        raise LayoutDecodeError("不支持的 COCL version=%d" % version)
    if grid != GRID_SIZE:
        raise LayoutDecodeError("grid=%d，期望 %d" % (grid, GRID_SIZE))
    need = COCL_HEADER_SIZE + n_build * 3 + n_wall * 2
    if len(blob) != need:
        raise LayoutDecodeError("长度不符：头部声明 %d，实际 %d" % (need, len(blob)))
    offset = COCL_HEADER_SIZE
    buildings: List[Tuple[str, int, int]] = []
    for _ in range(n_build):
        tid, x, y = blob[offset], blob[offset + 1], blob[offset + 2]
        offset += 3
        if tid not in SYNTHETIC_BUILDING_TYPES:
            raise LayoutDecodeError("未知 type_id=%d" % tid)
        if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
            raise LayoutDecodeError("tile 越界：(%d, %d)" % (x, y))
        buildings.append((SYNTHETIC_BUILDING_TYPES[tid], x, y))
    walls: List[Tuple[int, int]] = []
    for _ in range(n_wall):
        x, y = blob[offset], blob[offset + 1]
        offset += 2
        if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
            raise LayoutDecodeError("wall tile 越界：(%d, %d)" % (x, y))
        walls.append((x, y))
    return DecodedLayout(buildings=tuple(buildings), walls=tuple(walls), codec="cocl")


def _layout_from_json(blob: bytes) -> DecodedLayout:
    """把 JSON 布局（layout.json 同 schema 的最小子集）解析成 DecodedLayout。"""
    try:
        data = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LayoutDecodeError("不是 JSON：%s" % exc)
    if not isinstance(data, dict) or not isinstance(data.get("buildings"), list):
        raise LayoutDecodeError("JSON 缺少 buildings 数组")
    grid = data.get("grid", GRID_SIZE)
    if grid != GRID_SIZE:
        raise LayoutDecodeError("grid=%r，期望 %d" % (grid, GRID_SIZE))
    buildings: List[Tuple[str, int, int]] = []
    for item in data["buildings"]:
        if not isinstance(item, dict):
            raise LayoutDecodeError("building 条目不是对象：%r" % (item,))
        type_name = item.get("type")
        tile = item.get("tile")
        if not isinstance(type_name, str) or not type_name:
            raise LayoutDecodeError("building.type 必须是非空字符串")
        if not isinstance(tile, (list, tuple)) or len(tile) != 2:
            raise LayoutDecodeError("building.tile 必须是 [x, y]")
        x, y = int(tile[0]), int(tile[1])
        if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
            raise LayoutDecodeError("tile 越界：(%d, %d)" % (x, y))
        buildings.append((type_name, x, y))
    walls: List[Tuple[int, int]] = []
    for item in data.get("walls") or []:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise LayoutDecodeError("wall 条目必须是 [x, y]")
        x, y = int(item[0]), int(item[1])
        if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
            raise LayoutDecodeError("wall tile 越界：(%d, %d)" % (x, y))
        walls.append((x, y))
    return DecodedLayout(buildings=tuple(buildings), walls=tuple(walls), codec="json")


# ---------------------------------------------------------------------------
# codec 链
# ---------------------------------------------------------------------------


def _raw_deflate(data: bytes) -> bytes:
    return zlib.decompress(data, -zlib.MAX_WBITS)


def _decompressors() -> List[Tuple[str, Callable[[bytes], bytes]]]:
    items: List[Tuple[str, Callable[[bytes], bytes]]] = [
        ("zlib", zlib.decompress),
        ("deflate-raw", _raw_deflate),
        ("gzip", gzip.decompress),
        ("bz2", bz2.decompress),
        ("lzma", lzma.decompress),
    ]
    try:  # brotli 可选，缺失不影响其余 codec
        import brotli  # type: ignore

        items.append(("brotli", brotli.decompress))
    except Exception:  # pragma: no cover - 环境无 brotli 时
        pass
    return items


def _codec_order() -> List[Tuple[str, Callable[[bytes], DecodedLayout]]]:
    order: List[Tuple[str, Callable[[bytes], DecodedLayout]]] = [
        ("cocl-raw", _layout_from_cocl),
        ("json-raw", _layout_from_json),
    ]
    for name, decompress in _decompressors():
        order.append(("cocl+" + name, lambda b, d=decompress: _layout_from_cocl(d(b))))
        order.append(("json+" + name, lambda b, d=decompress: _layout_from_json(d(b))))
    return order


def decode_layout_payload(raw: bytes) -> LayoutDecodeResult:
    """按 codec 链尝试把 payload 字节还原成阵型；真实 opaque token 会全部失败。"""
    attempts: List[CodecAttempt] = []
    for name, codec in _codec_order():
        try:
            decoded = codec(raw)
        except Exception as exc:  # 每个 codec 的失败都记录，便于诊断
            attempts.append(CodecAttempt(codec=name, ok=False, detail="%s: %s" % (type(exc).__name__, exc)))
            continue
        attempts.append(
            CodecAttempt(
                codec=name,
                ok=True,
                detail="decoded %d buildings / %d walls" % (len(decoded.buildings), len(decoded.walls)),
            )
        )
        # 解码成功时 payload_kind 反映命中 codec 的族（COCL 合成 / JSON 布局），
        # 而不是容器分类；失败时才退回原始字节分类。
        decoded_kind = "cocl-synthetic" if name.startswith("cocl") else "json-layout"
        return LayoutDecodeResult(
            ok=True,
            codec=name,
            layout=decoded,
            attempts=tuple(attempts),
            payload_kind=decoded_kind,
        )
    return LayoutDecodeResult(
        ok=False,
        codec=None,
        layout=None,
        attempts=tuple(attempts),
        payload_kind=classify_payload(raw),
    )


# ---------------------------------------------------------------------------
# layout.json schema 适配
# ---------------------------------------------------------------------------


def to_layout_json(
    decoded: DecodedLayout,
    *,
    name: str,
    note: Optional[str] = None,
    source: str = "baselink",
    conf: float = 1.0,
) -> Dict[str, object]:
    """把解码结果转成与 bases/th16/*/layout.json 相同的 schema。

    顶层键固定为 name / grid / note / buildings / walls；
    building 条目固定为 type / tile / source / conf / note。
    """
    if decoded is None:
        raise LayoutDecodeError("decoded 不能为空")
    buildings = [
        {
            "type": type_name,
            "tile": [int(x), int(y)],
            "source": source,
            "conf": conf,
            "note": "",
        }
        for type_name, x, y in decoded.buildings
    ]
    walls = [[int(x), int(y)] for x, y in decoded.walls]
    if note is None:
        note = "由 baselink codec=%s 解码；坐标口径与 layout.json 一致（整数格号，左上角）。" % decoded.codec
    return {
        "name": name,
        "grid": GRID_SIZE,
        "note": note,
        "buildings": buildings,
        "walls": walls,
    }


def undecodable_layout(link: BaseLink, reason: str, *, name: Optional[str] = None) -> Dict[str, object]:
    """无法解码时输出同 schema 的空布局，原因写进 note（便于下游无感消费）。"""
    if name is None:
        name = "baselink_th%d_%s_%s" % (link.town_hall, link.village, link.payload[-6:])
    return {
        "name": name,
        "grid": GRID_SIZE,
        "note": reason,
        "buildings": [],
        "walls": [],
    }


def build_layout_from_link(
    url: str,
    *,
    name: Optional[str] = None,
    allow_empty: bool = True,
) -> Dict[str, object]:
    """链接 -> layout.json 同 schema。解不出时：allow_empty=True 返回空布局，否则抛错。"""
    link = parse_link(url)
    raw = decode_payload(link.payload)
    result = decode_layout_payload(raw)
    if result.ok and result.layout is not None:
        return to_layout_json(
            result.layout,
            name=name or "baselink_th%d_%s" % (link.town_hall, link.village),
        )
    reason = (
        "baselink 无法离线解码：payload %d 字节，分类=%s；真实格式未公开，见 baselink.py 文档。"
        % (len(raw), result.payload_kind)
    )
    if allow_empty:
        return undecodable_layout(link, reason, name=name)
    raise LayoutDecodeError(reason)


# ---------------------------------------------------------------------------
# 汇总分析（CLI / 报告用）
# ---------------------------------------------------------------------------


def analyze_link(url: str) -> Dict[str, object]:
    """完整分析一条分享链接，返回 JSON 友好的报告字典。"""
    link = parse_link(url)
    raw = decode_payload(link.payload)
    envelope = parse_envelope(raw)
    result = decode_layout_payload(raw)
    report: Dict[str, object] = {
        "url": link.url,
        "town_hall": link.town_hall,
        "village": link.village,
        "village_name": link.village_name,
        "language": link.language,
        "payload": link.payload,
        "payload_chars": len(link.payload),
        "payload_bytes": len(raw),
        "payload_hex": raw.hex(),
        "envelope": envelope.to_dict(),
        "payload_kind": result.payload_kind,
        "codec_attempts": [attempt.to_dict() for attempt in result.attempts],
        "decoded": result.ok,
        "codec": result.codec,
        "building_count": len(result.layout.buildings) if result.layout else 0,
        "wall_count": len(result.layout.walls) if result.layout else 0,
        "link": link.to_dict(),
        "decoded_layout": (
            {
                "codec": result.layout.codec,
                "grid": result.layout.grid,
                "buildings": [[t, x, y] for t, x, y in result.layout.buildings],
                "walls": [[x, y] for x, y in result.layout.walls],
            }
            if result.layout is not None
            else None
        ),
    }
    if result.payload_kind == "opaque-token-v1":
        report["opaque_token"] = {
            "raw_len": len(raw),
            "declared_length": envelope.declared_length,
            "kind": envelope.kind,
            "value_len": len(envelope.value),
            "value_hex": envelope.value.hex(),
            "consistent": envelope.consistent,
            "conclusion": (
                "链接 id 是 24 字节不透明引用（8 字节信封 + 16 字节值）；"
                "该体量无法编码 44x44 全量建筑，离线不可还原，需游戏客户端/服务器解析。"
            ),
        }
    return report
