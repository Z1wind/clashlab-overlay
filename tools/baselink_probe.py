#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""baselink 探针：解析 Clash of Clans 分享阵型链接并输出诊断报告。

用法示例::

    # 单条真实链接
    python tools/baselink_probe.py --url "https://link.clashofclans.com/en?action=OpenLayout&id=TH16%3AWB%3A..."

    # 扫描本项目所有 bases/th16/*/source.json 的 copy_link
    python tools/baselink_probe.py --bases-dir bases/th16

    # 机器可读
    python tools/baselink_probe.py --bases-dir bases/th16 --json

    # 若 codec 链成功解出（例如测试用的合成样本），写出 layout.json
    python tools/baselink_probe.py --url "<synthetic-link>" --write-layout out/baselink/layout.json

退出码：0 = 全部解析成功；2 = 存在解析失败；3 = 无法写出 layout（未解码）。
"""
import argparse
import glob
import json
import os
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from clashlab import baselink  # noqa: E402

DEFAULT_BASES_DIR = os.path.join(ROOT, "bases", "th16")


def make_url_from_id(ident):
    return "https://link.clashofclans.com/en?action=OpenLayout&id=" + quote(ident, safe="")


def make_url_from_payload(payload, th, village):
    return make_url_from_id("TH%d:%s:%s" % (th, village, payload))


def iter_source_links(bases_dir):
    """扫描 <bases_dir>/*/source.json 里的 copy_link。"""
    pattern = os.path.join(bases_dir, "*", "source.json")
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            yield path, None, "读取失败：%s" % exc
            continue
        link = data.get("copy_link")
        if isinstance(link, str) and link:
            yield path, link, None
        else:
            yield path, None, "source.json 无 copy_link"


def format_report(report, index=None, total=None, source=""):
    lines = []
    head = "[%d/%d] %s" % (index, total, source) if index and total else (source or "")
    if head:
        lines.append(head)
    lines.append("  url: %s" % report["url"])
    lines.append(
        "  town_hall=%d village=%s (%s) language=%r"
        % (report["town_hall"], report["village"], report["village_name"], report["language"])
    )
    lines.append(
        "  payload: %d chars -> %d bytes  hex=%s"
        % (report["payload_chars"], report["payload_bytes"], report["payload_hex"])
    )
    env = report["envelope"]
    lines.append(
        "  envelope: declared_length=%r kind=%r value_len=%d consistent=%s"
        % (env["declared_length"], env["kind"], env["value_len"], env["consistent"])
    )
    lines.append("  payload_kind: %s" % report["payload_kind"])
    lines.append("  codec attempts (%d):" % len(report["codec_attempts"]))
    for attempt in report["codec_attempts"]:
        mark = "OK  " if attempt["ok"] else "FAIL"
        lines.append("    - %s %-14s %s" % (mark, attempt["codec"], attempt["detail"]))
    if report["decoded"]:
        lines.append(
            "  decoded=True codec=%s buildings=%d walls=%d"
            % (report["codec"], report["building_count"], report["wall_count"])
        )
    else:
        lines.append("  decoded=False")
        opaque = report.get("opaque_token")
        if opaque:
            lines.append("  结论：%s" % opaque["conclusion"])
        else:
            lines.append("  结论：未命中任何已知 codec；真实格式未知。")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Clash of Clans 分享阵型链接（OpenLayout）解析探针",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--url", help="完整分享链接")
    src.add_argument("--id", help="链接里的 id，如 TH16:WB:AAAA...")
    src.add_argument("--payload", help="仅 base64url payload（需配合 --th/--village）")
    src.add_argument(
        "--bases-dir",
        nargs="?",
        const=DEFAULT_BASES_DIR,
        help="扫描该目录下 */source.json 的 copy_link（缺省 bases/th16）",
    )
    parser.add_argument("--th", type=int, default=16, help="--payload 时的 TH 等级（默认 16）")
    parser.add_argument("--village", default="WB", choices=["HV", "WB"], help="--payload 时的村庄类型")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument("--write-layout", metavar="PATH", help="解码成功时写出 layout.json 同 schema 文件")
    args = parser.parse_args(argv)

    urls = []
    sources = []
    if args.url:
        urls.append(args.url)
        sources.append("--url")
    elif args.id:
        urls.append(make_url_from_id(args.id))
        sources.append("--id")
    elif args.payload:
        urls.append(make_url_from_payload(args.payload, args.th, args.village))
        sources.append("--payload")
    else:
        bases_dir = args.bases_dir or DEFAULT_BASES_DIR
        found = 0
        for path, link, error in iter_source_links(bases_dir):
            rel = os.path.relpath(path, ROOT)
            if error:
                print("[skip] %s：%s" % (rel, error))
                continue
            urls.append(link)
            sources.append(rel)
            found += 1
        if found == 0:
            print("在 %s 下没找到任何 copy_link" % bases_dir)
            return 2

    exit_code = 0
    reports = []
    for index, (url, source) in enumerate(zip(urls, sources), start=1):
        try:
            report = baselink.analyze_link(url)
        except baselink.BaseLinkError as exc:
            exit_code = 2
            if args.json:
                reports.append({"source": source, "url": url, "error": str(exc), "code": exc.code})
            else:
                print("[%d/%d] %s" % (index, len(urls), source))
                print("  ERROR %s" % exc)
            continue
        reports.append(report)
        if not args.json:
            print(format_report(report, index, len(urls), source))
            print()

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))

    if args.write_layout:
        if len(reports) != 1 or not isinstance(reports[0], dict) or not reports[0].get("decoded"):
            print("无法写出 layout：需要恰好一条已解码的链接（当前 decoded=%r）" % (
                reports[0].get("decoded") if reports and isinstance(reports[0], dict) else None,
            ), file=sys.stderr)
            return 3
        report = reports[0]
        decoded = report["decoded_layout"]
        layout = baselink.to_layout_json(
            baselink.DecodedLayout(
                buildings=tuple(tuple(item) for item in decoded["buildings"]),
                walls=tuple(tuple(item) for item in decoded["walls"]),
                codec=decoded["codec"],
            ),
            name="baselink_th%d_%s" % (report["town_hall"], report["village"]),
        )
        out_path = os.path.abspath(args.write_layout)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(layout, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print("已写出 %s（%d buildings / %d walls）" % (out_path, len(layout["buildings"]), len(layout["walls"])))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
