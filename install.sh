#!/usr/bin/env bash
#
# install.sh — 一键安装 git-repo-chronicle 技能到本机已检测到的工具
#
# 支持: Claude Code (~/.claude/skills)、Codex CLI (~/.codex/skills)、
#       Cursor (~/.cursor/skills)、项目级 .claude/skills(需在仓库根目录运行)
#
# 用法:  ./install.sh [--force]   (--force 覆盖更新已安装的副本)
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/skills/git-repo-chronicle"
[ -d "$SRC" ] || { echo "错误: 找不到 $SRC" >&2; exit 1; }

FORCE=""
[ "${1:-}" = "--force" ] && FORCE=1

installed=0
found=0
for target in "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.cursor/skills" ".claude/skills"; do
  dest="$target/git-repo-chronicle"
  if [ -d "$target" ]; then
    found=1
    if [ -e "$dest" ]; then
      if [ -n "$FORCE" ]; then
        rm -rf "$dest"
        cp -R "$SRC" "$dest"
        echo "已更新: $dest"
        installed=1
      else
        echo "已存在,跳过: $dest (加 --force 可覆盖更新)"
      fi
    else
      cp -R "$SRC" "$dest"
      echo "已安装: $dest"
      installed=1
    fi
  fi
done

if [ "$found" -eq 0 ]; then
  echo "未检测到任何技能目录。可手动安装:"
  echo "  mkdir -p ~/.claude/skills && cp -R $SRC ~/.claude/skills/"
  echo "或通过插件方式安装(Claude Code): cc plugin install <本仓库地址>"
fi
