#!/usr/bin/env python3
"""Render a year of per_month.tsv as a standalone, accessible SVG (stdlib only)."""

import argparse
import datetime as dt
from html import escape
from pathlib import Path
import re


def read_months(path):
    """Read the export's month / commits / authors columns without losing zeroes."""
    rows = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 3 or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", fields[0]):
            raise ValueError(f"第 {line_number} 行需为 月份<TAB>提交数<TAB>作者数")
        month = fields[0]
        try:
            commits, authors = map(int, fields[1:])
        except ValueError:
            raise ValueError(f"第 {line_number} 行的统计值必须是整数") from None
        if commits < 0 or authors < 0 or authors > commits:
            raise ValueError(f"第 {line_number} 行的提交数/作者数不合理")
        if month in rows:
            raise ValueError(f"月份重复: {month}")
        rows[month] = (commits, authors)
    return rows


def render(rows, year, through, title, revision, basis):
    if not 1 <= year <= 9999 or year > through.year:
        raise ValueError("年份必须在采集截止日期内")
    last_month = through.month if through.year == year else 12
    for month in rows:
        if month.startswith(f"{year:04d}-") and int(month[5:]) > last_month:
            raise ValueError("输入包含采集截止月份之后的数据，请核对 --through")
    counts = [rows.get(f"{year:04d}-{m:02d}", (0, 0))[0] for m in range(1, last_month + 1)]
    peak = max(counts + [1])
    summary = "；".join(f"{m}月 {counts[m-1]} 条" if m <= last_month else f"{m}月未覆盖"
                       for m in range(1, 13))
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" viewBox="0 0 960 360" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)} · {year} 提交活动</title>',
        f'<desc id="desc">截至 {through.isoformat()}，合计 {sum(counts)} 条提交。{escape(summary)}。{escape(basis)}</desc>',
        '<rect width="960" height="360" rx="16" fill="#faf7f0"/>',
        '<g font-family="system-ui, sans-serif" fill="#302d29">',
        f'<text x="40" y="38" font-size="22" font-weight="700">{escape(title)} · {year} 提交活动</text>',
        f'<text x="40" y="64" font-size="13">截至 {through.isoformat()} · 已覆盖月份共 {sum(counts)} 条提交</text>',
        '<line x1="42" y1="260" x2="918" y2="260" stroke="#b3aa9b"/>',
    ]
    for month in range(1, 13):
        x = 50 + (month - 1) * 73
        if month <= last_month:
            count = counts[month - 1]
            height = count / peak * 150
            out.append(f'<rect data-month="{year:04d}-{month:02d}" data-count="{count}" x="{x}" y="{260-height:.2f}" width="48" height="{height:.2f}" rx="4" fill="#437b6a"/>')
            out.append(f'<text x="{x+24}" y="{248-height:.2f}" text-anchor="middle" font-size="14">{count}</text>')
        else:
            out.append(f'<rect data-month="{year:04d}-{month:02d}" data-status="uncovered" x="{x}" y="110" width="48" height="150" rx="4" fill="#ebe6dc"/>')
            out.append(f'<text x="{x+24}" y="196" text-anchor="middle" font-size="12" fill="#756d60">未覆盖</text>')
        out.append(f'<text x="{x+24}" y="282" text-anchor="middle" font-size="13">{month:02d}</text>')
    out += [
        f'<text x="40" y="314" font-size="12">{escape(basis)}</text>',
        f'<text x="40" y="337" font-size="12">快照 {escape(revision)} · 截止月可能不完整；未覆盖不等于零提交</text>',
        '</g></svg>',
    ]
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="dump_git_history.sh 导出的 per_month.tsv")
    parser.add_argument("output", type=Path, help="输出 SVG 文件")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--through", type=dt.date.fromisoformat, required=True, help="数据覆盖截止日 YYYY-MM-DD")
    parser.add_argument("--revision", required=True, help="本次采集固定的 commit 或范围")
    parser.add_argument("--title", default="提交活动")
    parser.add_argument("--basis", default="committer 日期原时区按月聚合 · 含 merge · 来源 per_month.tsv")
    args = parser.parse_args()
    try:
        svg = render(read_months(args.input), args.year, args.through, args.title, args.revision, args.basis)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(svg, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"错误: {exc}\n")
    print(args.output)


if __name__ == "__main__":
    main()
