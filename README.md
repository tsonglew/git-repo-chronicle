# git-repo-chronicle · 项目开发编年史

读一个项目多年的提交记录,再把 release、issue、论坛讨论、RSS、新闻和当时的时代背景合进来,整理成一部《项目开发编年史》。按年分章,每条提交都能追到哈希,代码主线与社区回声两条线对照着写,结论先放在开头。

## 示例

### OpenClaw 项目开发编年史

<img width="627" height="940" alt="image" src="https://github.com/user-attachments/assets/326f6f0f-e672-4ff5-bbe8-b1da8de83cef" />


## 安装

六条路,任选一条。

| 方式 | 命令 | 适用 |
|---|---|---|
| npx 免克隆 | `npx -y github:tsonglew/git-repo-chronicle` | 仓库推上 GitHub 就能用,不用等发布 |
| npx(npm 包) | `npx -y git-repo-chronicle` | npm 包发布之后 |
| npm 全局 | `npm install -g git-repo-chronicle` | 装一次,长期用 |
| 一键脚本 | `git clone https://github.com/tsonglew/git-repo-chronicle && cd git-repo-chronicle && ./install.sh` | 机器上没有 Node |
| cc 插件 | `cc plugin install https://github.com/tsonglew/git-repo-chronicle` | 只用 Claude Code |
| 手动复制 | 见下面的表 | 其他任何工具 |

安装器会把技能复制到本机检测到的技能目录。重复运行不会覆盖,想更新就加 `--force`。

| 工具 | 复制到 |
|---|---|
| Claude Code | `~/.claude/skills/git-repo-chronicle/`(个人)或项目 `.claude/skills/` |
| Codex CLI | `~/.codex/skills/git-repo-chronicle/`(或 `codex skill add` 安装) |
| Cursor | 项目 `.cursor/skills/` 或 `~/.cursor/skills/` |
| 其他 IDE | 任何支持 Agent Skills(SKILL.md + frontmatter)的工具 |

技能目录遵循 Agent Skills 规范,只有一个 `SKILL.md` 加几个文档和脚本,没有任何运行时依赖。

## 使用

装好后对 AI 说下面这句。

> 给 https://github.com/xxx/yyy 写一部项目开发编年史,中文,输出到 docs/notes/

或者这句。

> 用 git-repo-chronicle 整理这个仓库的七年开发史,结合 release、issue 和论坛讨论,结论先行,每条提交可溯源

AI 会先克隆仓库,用脚本把提交和元数据导出,再检索 release、issue、论坛、RSS、新闻,按年归纳,照模板成文,最后逐条核对来源。

想让成稿带手绘风插图,给 AI 生图服务的 base_url、api_key、model 三项配置(OpenAI 兼容接口即可),它会按编年史风格给封面和章节配图。没有配置会自动跳过,不影响出稿。

## 数据从哪来

六类来源。

1. git 提交,主线,逐条核对
2. release 和 tag,官方叙事的骨架
3. issue 和 PR,需求和争议的证据
4. 论坛讨论,社区回声,和代码互相印证
5. RSS,release 与提交的 feed,拿到精确时间线
6. 新闻与时代背景,解释为什么在那个时间点做那件事

论坛和代码互相印证是最有意思的部分。论坛先有人喊"Linux 版什么时候有",几个月后代码里出现跨平台迁移的提交,这种时刻就是编年史的关节,写作模板里叫互文时刻。

## 成稿长这样

开头几行取自示例,全文见 `skills/git-repo-chronicle/examples/chronicle-excerpt.md`。

> # 《项目开发编年史,从 0 到 1 的八年》
>
> 整理日期 2026-08-07
> 数据来源 1,204 条 git 提交逐一核对、37 个 release、218 个 issue、论坛 89 帖、新闻 6 篇
> 核心结论 一个人撑起前四年,社区接力补完第五年

正文按年分章,每章一句"一句话"开头,提交一行一条,都能追到哈希和 PR 编号。关键节点配 Mermaid 架构图和流程图,GitHub 打开即渲染。文末配 PR 时间线、论坛数据附录和数据方法论。

## 在线示例

OpenClaw 编年史的在线书,由本 skill 生成并部署到 Vercel。

<https://openclaw-chronicle.vercel.app>

15 章,每章一张手绘插图,架构图在浏览器端渲染,纯静态零构建。同一份源稿还产出 EPUB 电子书,转换脚本零依赖。

## 目录结构

```
├── .claude-plugin/plugin.json        Claude Code 插件清单
├── package.json                      npm 包清单(npx 安装入口)
├── install.js                        npm/npx 安装器(跨平台,Node)
├── install.sh                        bash 安装脚本
└── skills/git-repo-chronicle/
    ├── SKILL.md                      核心工作流(触发与四阶段流程)
    ├── references/
    │   ├── chronicle-structure.md    编年史结构模板与写作风格
    │   └── data-sources.md           六类数据源采集手册
    ├── scripts/
    │   ├── dump_git_history.sh       git 提交导出 + 年度/作者统计
    │   └── fetch_github_meta.sh      release/issue/PR 元数据(gh)
    └── examples/
        └── chronicle-excerpt.md      编年史片段格式示例
```

## 常见问题

- 没装 gh?`fetch_github_meta.sh` 会打印 GitHub API 的兜底命令,`git tag` 永远能用。
- 仓库有上万提交?技能会自动改用里程碑窗口精读加月度聚合,文末标注口径。
- 论坛抓不到?用站点搜索和存档站代替,附录注明覆盖率。
- 想改输出风格?改 `references/chronicle-structure.md` 里的模板。

## 写给维护者

- 发布 npm 包。`npm version patch && npm publish`,下次改版重复这两步。
- 发布前检查包内容。`npm pack --dry-run`,确认 `skills/` 目录在里面。
- 技能文件有改动后,用户端加 `--force` 重装即可更新。
- 许可证 MIT,见 `LICENSE`。
