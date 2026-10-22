#!/usr/bin/env bash
#
# dump_git_history.sh — 将 git 提交历史导出为结构化数据,供编年史写作使用
#
# 用法:  dump_git_history.sh <仓库路径> <输出目录> [--first-parent]
#
# 输出文件:
#   commits.tsv       哈希 | 作者 | 邮箱 | committer ISO日期 | 标题(每条一行)
#   commits_full.log  完整日志(含正文),供精读
#   per_year.tsv      年份 | 提交数 | 去重作者数
#   per_month.tsv     月份 | 提交数 | 去重作者数(数据速览用)
#   tags.tsv          tag名 | 日期(版本节奏用)
#   per_author.tsv    提交数 | 作者 | 邮箱(降序)
#   meta.txt          总提交数、首末提交、分支、tag 数
#
# 依赖: 仅 git(bash 3.2+ 即可,兼容 macOS 自带环境)
set -euo pipefail

REPO="${1:?用法: dump_git_history.sh <仓库路径> <输出目录> [--first-parent]}"
OUT="${2:?用法: dump_git_history.sh <仓库路径> <输出目录> [--first-parent]}"
FLAG="${3:-}"

if [ "$#" -gt 3 ] || { [ -n "$FLAG" ] && [ "$FLAG" != "--first-parent" ]; }; then
  echo "错误: 仅支持可选参数 --first-parent" >&2
  exit 1
fi
git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || { echo "错误: $REPO 不是 git 仓库" >&2; exit 1; }
mkdir -p "$OUT"
# 输出路径相对于调用目录解析,不能随 cd 到仓库后改变。
OUT="$(cd "$OUT" && pwd)"
cd "$REPO"

LOG_ARGS=(--date=iso-strict)
[ "$FLAG" = "--first-parent" ] && LOG_ARGS+=(--first-parent)

# 1. 结构化 TSV。固定在同一 HEAD,统计统一从这个导出读取。
# 按 committer 日期的原时区聚合;它不一定等于 PR 的 mergedAt。
if HEAD_COMMIT=$(git rev-parse --verify HEAD 2>/dev/null); then
  git log "${LOG_ARGS[@]}" --pretty=format:'%H%x09%an%x09%ae%x09%cI%x09%s' "$HEAD_COMMIT" | awk '{print}' > "$OUT/commits.tsv"

  # 2. 完整日志同时保留作者时间,便于辨别迟合并与 cherry-pick。
  git log "${LOG_ARGS[@]}" --pretty=format:'commit %H%nAuthor: %an <%ae>%nAuthorDate: %aI%nCommitDate: %cI%n%n    %s%n%n%b%n%n---' "$HEAD_COMMIT" | awk '{print}' > "$OUT/commits_full.log"
else
  HEAD_COMMIT="unborn"
  : > "$OUT/commits.tsv"
  : > "$OUT/commits_full.log"
fi

# 3. 年度统计: 年份 | 提交数 | 去重作者数
awk -F'\t' '{year=substr($4,1,4); n[year]++; if (!seen[year FS $3]++) au[year]++} END{for (y in n) print y "\t" n[y] "\t" au[y]}' "$OUT/commits.tsv" \
  | sort > "$OUT/per_year.tsv"

# 3b. 月度统计: 月份 | 提交数 | 去重作者数(数据速览用)
awk -F'\t' '{month=substr($4,1,7); n[month]++; if (!seen[month FS $3]++) au[month]++} END{for (m in n) print m "\t" n[m] "\t" au[m]}' "$OUT/commits.tsv" \
  | sort > "$OUT/per_month.tsv"

# 3c. tag 列表: tag名 | 日期(版本节奏用)
# 注意 git tag 的 --format 不支持 %x09 转义,用 printf 嵌入真实 tab
TAG_FMT=$(printf '%%(refname:short)\t%%(creatordate:short)')
git tag -l --sort=creatordate --format="$TAG_FMT" > "$OUT/tags.tsv"

# 4. 作者统计: 提交数 | 作者 | 邮箱
awk -F'\t' '{n[$2 FS $3]++} END{for (a in n) print n[a] "\t" a}' "$OUT/commits.tsv" \
  | sort -rn > "$OUT/per_author.tsv"

# 5. 元信息
{
  echo "总提交数: $(wc -l < "$OUT/commits.tsv" | tr -d ' ')"
  awk -F'\t' 'END{if (NR) print "首个提交: " substr($1,1,7) " " $4 " " $5; else print "首个提交: 无"}' "$OUT/commits.tsv"
  awk -F'\t' 'NR==1{print "最近提交: " substr($1,1,7) " " $4 " " $5} END{if (!NR) print "最近提交: 无"}' "$OUT/commits.tsv"
  echo "当前分支: $(git branch --show-current)"
  echo "截点 commit: $HEAD_COMMIT"
  echo "提交口径: ${FLAG:---all-reachable-from-HEAD}(含 merge)"
  echo "日期口径: committer ISO 日期,按原时区年月聚合;不等同于 PR mergedAt"
  echo "tag 数:   $(git tag | wc -l | tr -d ' ')"
} > "$OUT/meta.txt"

echo "完成。输出目录: $OUT"
echo "  commits.tsv    $(wc -l < "$OUT/commits.tsv" | tr -d ' ') 条提交"
echo "  per_year.tsv   $(wc -l < "$OUT/per_year.tsv" | tr -d ' ') 个年份"
echo "  per_month.tsv  $(wc -l < "$OUT/per_month.tsv" | tr -d ' ') 个月份"
echo "  tags.tsv       $(wc -l < "$OUT/tags.tsv" | tr -d ' ') 个 tag"
echo "  per_author.tsv $(wc -l < "$OUT/per_author.tsv" | tr -d ' ') 位作者"
