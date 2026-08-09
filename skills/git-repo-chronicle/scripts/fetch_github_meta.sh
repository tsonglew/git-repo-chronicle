#!/usr/bin/env bash
#
# fetch_github_meta.sh — 拉取 GitHub release / issue / PR 元数据,供编年史写作使用
#
# 用法:  fetch_github_meta.sh <owner/repo> <输出目录>
#
# 输出文件:
#   releases.json  tagName, publishedAt, name(注意:部分实例的 release 没有 body 字段,
#                  带 body 会报 Unknown JSON field,故不请求)
#   issues.json    number, title, createdAt, closedAt, state, labels
#   prs.json       number, title, mergedAt, createdAt, state, labels
#
# 依赖:  gh CLI(https://cli.github.com)。未安装时打印 API 兜底提示,不中断流程。
# 已知坑: 仓库可能禁用 issue(报 disabled issues,issues.json 为空)、
#          可能没有 PR(prs.json 为空)。此时用提交消息里的 #N 编号重建 PR 时间线,
#          见 data-sources.md。
set -euo pipefail

REPO="${1:?用法: fetch_github_meta.sh <owner/repo> <输出目录>}"
OUT="${2:?用法: fetch_github_meta.sh <owner/repo> <输出目录>}"
mkdir -p "$OUT"

if command -v gh >/dev/null 2>&1; then
  echo "使用 gh 抓取 $REPO ..."

  gh release list --repo "$REPO" --limit 200 \
      --json tagName,publishedAt,name > "$OUT/releases.json" || \
      { echo "警告: release 抓取失败(仓库可能无 release)" >&2; : > "$OUT/releases.json"; }

  gh issue list --repo "$REPO" --state all --limit 500 \
      --json number,title,createdAt,closedAt,state,labels > "$OUT/issues.json" || \
      { echo "警告: issue 抓取失败" >&2; : > "$OUT/issues.json"; }

  gh pr list --repo "$REPO" --state all --limit 500 \
      --json number,title,mergedAt,createdAt,state,labels > "$OUT/prs.json" || \
      { echo "警告: PR 抓取失败" >&2; : > "$OUT/prs.json"; }

  count() { [ -f "$1" ] && { jq length "$1" 2>/dev/null || echo 0; } || echo 0; }
  echo "完成: release $(count "$OUT/releases.json") 个 / issue $(count "$OUT/issues.json") 个 / PR $(count "$OUT/prs.json") 个"
else
  echo "未检测到 gh。安装 gh(https://cli.github.com)后重跑可获得完整 release/issue/PR 数据。"
  echo "兜底方式(GitHub API,未认证 60 次/小时):"
  echo "  curl -s \"https://api.github.com/repos/$REPO/releases?per_page=100&page=1\""
  echo "  curl -s \"https://api.github.com/repos/$REPO/issues?state=all&per_page=100&page=1\""
fi
