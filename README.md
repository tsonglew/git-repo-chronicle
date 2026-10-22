# git-repo-chronicle · 项目开发编年史

读一个项目多年的提交记录,再把 release、issue、论坛讨论、RSS、新闻和当时的时代背景合进来,整理成一部《项目开发编年史》。按年分章,每条提交都能追到哈希,代码主线与社区回声两条线对照着写,结论先放在开头。

## 在线示例

### DeepSeek Harness 开发编年史

https://dsh-chronicle-duv8yxo8n-tsonglews-projects.vercel.app/

<img width="1144" height="928" alt="image" src="https://github.com/user-attachments/assets/ffb50dc7-0d4f-490b-8d3f-80b7ecac5edc" />


### OpenClaw 编年史

https://openclaw-chronicle.vercel.app

<img width="1414" height="874" alt="image" src="https://github.com/user-attachments/assets/f98878b8-7ba4-4a1f-a4f0-a6d74ef492c4" />


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

技能目录遵循 Agent Skills 规范,由 `SKILL.md`、参考文档和脚本组成。安装器需要 Node.js 16.7+ 或 Bash;采集历史需要 Git 和 Bash,活动图与增量续写需要 Python 3.8+,与 EPUB 脚本一样仅使用标准库,GitHub 元数据采集另需 `gh`。

## 使用

装好后对 AI 说下面这句。

> 给 https://github.com/xxx/yyy 写一部项目开发编年史,中文,输出到 docs/notes/

或者这句。

> 用 git-repo-chronicle 整理这个仓库的七年开发史,结合 release、issue 和论坛讨论,结论先行,每条提交可溯源

AI 会先克隆仓库,用脚本把提交和元数据导出,再检索 release、issue、论坛、RSS、新闻,按年归纳,照模板成文,最后逐条核对来源。

想让成稿带手绘风插图,给 AI 生图服务的 base_url、api_key、model 三项配置(OpenAI 兼容接口即可),它会按编年史风格给封面和章节配图。没有配置会自动跳过,不影响出稿。

已有编年史时,可以接着说。

> 按上次保存的截点续写这部编年史,只追加新章节或近况,保留旧章正文。发现错误时追加勘误。

续写前先校验旧稿和截点,按 commit 范围采集新增代码,按发布时间筛选 release 与社区材料;验证通过后才追加并推进截点。截点文件格式与完整命令见[增量续写指南](skills/git-repo-chronicle/references/incremental.md)。

## 叙事与核验能力

| 能力 | 使用方式 |
|---|---|
| 三幕梗概 | 开篇约 300–800 字讲起因、转折、现状,关键判断带 commit/release 来源 |
| 章节类型 | 默认使用「初创 · 具体事件」等类型标题,提供中英词表并允许项目自定义 |
| 章首节奏图 | 从月度提交 TSV 生成 SVG,标明截点、日期与 merge 口径 |
| 贡献者指纹 | 对照提交、改动路径与代表 commit,讲清谁推动了哪条主线 |
| 历史代码锚点 | 关键结论旁链接固定 SHA 的 tree/blob,或给出只读 `git show` 命令 |
| 社区来源清单 | 配置论坛、Reddit、HN、发行说明与博客 RSS,失败写明「未获取」与原因 |
| 代码存活附录 | 大重写或多年仓库按需引用外部分析结果,附统计范围、局限及正文互链 |
| 增量续写 | 保存截点与旧稿摘要,只追加新章或勘误,防止重复追加与无声改写 |

社区来源配置可从 [community-sources.json](skills/git-repo-chronicle/examples/community-sources.json) 复制,采集记录参考 [community-records.json](skills/git-repo-chronicle/examples/community-records.json)。配置 URL 是检索入口,具体社区反应仍需读取帖子原文并保存来源证据。采集失败不代表无人讨论。

活动图脚本可直接使用导出数据,无需生图服务。以下命令在技能目录运行,先导出目标仓库,再用随包附带的固定历史数据演示绘图。绘制目标仓库时改用导出的 TSV,并将年份、截止日、revision、标题改为实际采集信息。

```bash
bash scripts/dump_git_history.sh /path/to/repo /tmp/chronicle-meta
python3 scripts/render_activity.py examples/data/repository-per-month.tsv /tmp/activity-2026.svg \
  --year 2026 --through 2026-08-14 --revision 52aa947 --title git-repo-chronicle
```

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

下面引用[本仓库真实历史样章的三幕梗概](skills/git-repo-chronicle/examples/repository-chronicle.md#三幕梗概),范围固定在 `52aa947`,不包含本次新增能力。

> 起因
>
> 2026 年 8 月 7 日,仓库的第一条提交把技能说明、结构模板和采集脚本一起放了进来。它要解决的事情已经写得具体,从 Git 提交出发,补上 release、issue 和论坛材料,写成一部按年展开、每条提交可追溯的项目历史。安装器负责把技能放进不同工具的目录,写作规则负责把零散记录接成文章。最初的交付物是 Markdown 长文,已有示例可以对照。[最初的仓库](https://github.com/tsonglew/git-repo-chronicle/tree/364ebe43a59d782d6321d67437572006395cb110)
>
> 转折
>
> 两天后,交付物开始走出 Markdown。`f843990` 加入标准库实现的 EPUB 转换脚本,同一天的 `b589328` 又增加在线书输出,让同一份源稿生成目录页和分章网页。项目此时要同时处理章节结构、图片引用与阅读呈现,出版规范也随之进入技能。文字写完只是其中一步,读者怎样打开它,已经落到了脚本里。[EPUB 实现](https://github.com/tsonglew/git-repo-chronicle/blob/f8439902218ce78591a3eb3d20946b341f126985/skills/git-repo-chronicle/scripts/md2epub.py)、[在线书实现](https://github.com/tsonglew/git-repo-chronicle/blob/b5893284e875cb6f25463c62a07ac1fad77766f6/skills/git-repo-chronicle/scripts/md2epub.py)
>
> 现状
>
> 到本次历史截点,写作工作流又多了一层明确的检查。8 月 10 日的 `b5bf19c` 将数字来源、真实哈希、数据速览、推断标注和缺失资料处理写成规则,并提供可直接填写的单章模板。这个短阶段留下的主线是采集、写作和出版逐步接起来,同时用规则减少成稿走样。现有记录能证明工具和规范的变化,还不能证明读者规模或社区评价;这些材料在本例中仍标为未获取。[当时的检查规则](https://github.com/tsonglew/git-repo-chronicle/blob/b5bf19ca8767c6792e08f8a1d3c230df7377d266/skills/git-repo-chronicle/SKILL.md)

完整样章包含类型标题、年度活动图、贡献者指纹和可点击的历史代码锚点。更长的格式示例见 [chronicle-excerpt.md](skills/git-repo-chronicle/examples/chronicle-excerpt.md),其中项目与数据为虚构演示。

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
    ├── SKILL.md                      核心工作流与校验清单
    ├── references/
    │   ├── chronicle-structure.md    编年史结构模板与写作风格
    │   ├── data-sources.md           六类数据源、社区配置与缺口降级
    │   ├── diagrams.md               架构图与章首活动图
    │   └── incremental.md            截点格式与增量续写
    ├── scripts/
    │   ├── dump_git_history.sh       git 提交导出 + 年度/作者统计
    │   ├── fetch_github_meta.sh      release/issue/PR 元数据(gh)
    │   ├── render_activity.py        月度提交 TSV → SVG 活动图
    │   └── chronicle_checkpoint.py   截点管理、增量筛选与追加
    └── examples/
        ├── chronicle-excerpt.md      编年史片段格式示例(虚构项目)
        ├── repository-chronicle.md   本项目真实历史与三幕梗概
        ├── community-sources.json   项目级来源配置
        └── community-records.json   来源证据与未获取记录样例
```

## 常见问题

- 没装 gh?`fetch_github_meta.sh` 会打印 GitHub API 的兜底命令,`git tag` 永远能用。
- 仓库有上万提交?技能会自动改用里程碑窗口精读加月度聚合,文末标注口径。
- 论坛抓不到?用站点搜索和存档站核实;仍拿不到就记录「未获取」及原因,不补写社区反应。
- 已经写过一版?使用[增量模式](skills/git-repo-chronicle/references/incremental.md),保留旧稿,追加新章或勘误。
- 想改输出风格?改 `references/chronicle-structure.md` 里的模板。

## 写给维护者

- 本地验证。`npm test` 运行安装器语法检查和真实 Git fixture 测试,需要 Node.js、Git、Bash、Python 3。测试在临时目录执行,不改本机已安装技能。
- 发布 npm 包。`npm version patch && npm publish`,下次改版重复这两步。
- 发布前检查包内容。`npm pack --dry-run`,确认 `skills/` 目录在里面。
- 技能文件有改动后,用户端加 `--force` 重装即可更新。
- 许可证 MIT,见 `LICENSE`。
