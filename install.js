#!/usr/bin/env node
/**
 * git-repo-chronicle 一键安装器(npm / npx 入口,跨平台,仅需 Node)
 *
 * 用法:  npx -y git-repo-chronicle [--force]
 *        npm install -g git-repo-chronicle && git-repo-chronicle
 *
 * 把 skills/git-repo-chronicle 复制到本机已检测到的技能目录:
 *   ~/.claude/skills        (Claude Code)
 *   ~/.codex/skills         (Codex CLI)
 *   ~/.cursor/skills        (Cursor)
 *   当前目录/.claude/skills (项目级)
 *
 * 重复运行幂等;加 --force 覆盖更新。
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const FORCE = process.argv.includes('--force');
const SRC = path.join(__dirname, 'skills', 'git-repo-chronicle');

if (!fs.existsSync(SRC)) {
  console.error(`错误: 找不到 ${SRC}(npm 包内容不完整,请检查安装来源)`);
  process.exit(1);
}

const targets = [
  path.join(os.homedir(), '.claude', 'skills'),
  path.join(os.homedir(), '.codex', 'skills'),
  path.join(os.homedir(), '.cursor', 'skills'),
  path.join(process.cwd(), '.claude', 'skills'),
];

let found = 0;

for (const target of targets) {
  const dest = path.join(target, 'git-repo-chronicle');
  if (!fs.existsSync(target)) continue;
  found = 1;

  if (fs.existsSync(dest)) {
    if (FORCE) {
      fs.rmSync(dest, { recursive: true, force: true });
      fs.cpSync(SRC, dest, { recursive: true });
      console.log(`已更新: ${dest}`);
    } else {
      console.log(`已存在,跳过: ${dest} (加 --force 可覆盖更新)`);
    }
  } else {
    fs.cpSync(SRC, dest, { recursive: true });
    console.log(`已安装: ${dest}`);
  }
}

if (!found) {
  console.log('未检测到任何技能目录。可手动安装:');
  console.log(`  mkdir -p ~/.claude/skills && cp -R ${SRC} ~/.claude/skills/`);
  console.log('或通过插件方式安装(Claude Code): cc plugin install <本仓库地址>');
}
