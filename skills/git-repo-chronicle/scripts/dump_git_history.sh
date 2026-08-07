#!/usr/bin/env bash
#
# dump_git_history.sh — 将 git 提交历史导出为结构化数据,供编年史写作使用
#
# 用法:  dump_git_history.sh <仓库路径> <输出目录> [--first-parent]
#
# 输出文件:
#   commits.tsv       哈希 | 作者 | 邮箱 | ISO日期 | 标题(每条一行)
#   commits_full.log  完整日志(含正文),供精读
#   per_year.tsv      年份 | 提交数 | 去重作者数
#   per_author.tsv    提交数 | 作者 | 邮箱(降序)
#   meta.txt          总提交数、首末提交、分支、tag 数
#
# 依赖: 仅 git(bash 3.2+ 即可,兼容 macOS 自带环境)
set -euo pipefail

REPO="${1:?用法: dump_git_history.sh <仓库路径> <输出目录> [--first-parent]}"
OUT="${2:?用法: dump_git_history.sh <仓库路径> <输出目录> [--first-parent]}"
FLAG="${3:-}"

[ -d "$REPO/.git" ] || { echo "错误: $REPO 不是 git 仓库" >&2; exit 1; }
mkdir -p "$OUT"
cd "$REPO"

LOG_ARGS=(--date=iso-strict)
[ "$FLAG" = "--first-parent" ] && LOG_ARGS+=(--first-parent)

# 1. 结构化 TSV(awk 确保末行换行,空仓库输出空文件)
git log "${LOG_ARGS[@]}" --pretty=format:'%H%x09%an%x09%ae%x09%ad%x09%s' | awk '{print}' > "$OUT/commits.tsv"

# 2. 完整日志(含正文)
git log "${LOG_ARGS[@]}" --pretty=format:'commit %H%nAuthor: %an <%ae>%nDate:   %ad%n%n    %s%n%n%b%n%n---' | awk '{print}' > "$OUT/commits_full.log"

# 3. 年度统计: 年份 | 提交数 | 去重作者数
git log "${LOG_ARGS[@]}" --pretty=format:'%ad%x09%ae' \
  | awk -F'\t' '{year=substr($1,1,4); n[year]++; if (!seen[year FS $2]++) au[year]++} END{for (y in n) print y "\t" n[y] "\t" au[y]}' \
  | sort > "$OUT/per_year.tsv"

# 4. 作者统计: 提交数 | 作者 | 邮箱
git log "${LOG_ARGS[@]}" --pretty=format:'%an%x09%ae' \
  | sort | uniq -c | sort -rn \
  | sed -E 's/^ *([0-9]+) /\1\t/' > "$OUT/per_author.tsv"

# 5. 元信息
{
  echo "总提交数: $(git rev-list --count HEAD)"
  echo "首个提交: $(git log --reverse --format='%h %ad %s' | head -1)"
  echo "最近提交: $(git log -1 --format='%h %ad %s')"
  echo "当前分支: $(git branch --show-current)"
  echo "tag 数:   $(git tag | wc -l | tr -d ' ')"
} > "$OUT/meta.txt"

echo "完成。输出目录: $OUT"
echo "  commits.tsv    $(wc -l < "$OUT/commits.tsv" | tr -d ' ') 条提交"
echo "  per_year.tsv   $(wc -l < "$OUT/per_year.tsv" | tr -d ' ') 个年份"
echo "  per_author.tsv $(wc -l < "$OUT/per_author.tsv" | tr -d ' ') 位作者"
