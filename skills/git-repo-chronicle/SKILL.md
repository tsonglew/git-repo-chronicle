---
name: git-repo-chronicle
description: 为有长期历史的 GitHub 项目撰写《项目开发编年史》。This skill should be used when the user asks to "写项目编年史", "整理项目开发历史", "做一部项目开发编年史", "项目开发史", "从零到一的七年", "把提交历史整理成编年史", "write a project chronicle", "chronicle this repo", or wants a narrative history of a codebase that combines commits, releases, issues, forum discussions, RSS, news, and the historical context of the era.
version: 0.1.0
---

# 项目开发编年史 (git-repo-chronicle)

## 用途

把一个有多年历史的 GitHub 项目的零散提交记录,与 release、issue、论坛讨论、RSS、新闻以及当时的时代背景互相印证,整理成一部可读、可溯源、有叙事主线的《项目开发编年史》。最终效果参考 Zircon 项目的开发编年史笔记(从 0 到 1 的七年)。写作要求是按年分章、每条提交可追溯、git 主线与社区回声双线并行、结论先行。结构模板与写作风格见 `references/chronicle-structure.md`。

## 何时使用

- 用户给出一个 GitHub 仓库地址或本地 git 仓库路径,要求"写编年史""项目历史""开发史""从零到一""chronicle"。
- 用户想理解一个项目为什么这样演进,比如架构决策、社区影响、时代背景、停更与复活。
- 产出为一份 Markdown 长文,含表格、时间线、附录,写入用户指定的路径。默认写到 `<仓库>/docs/notes/项目开发编年史-从零到一.md`,只读仓库写到当前目录。

## 工作流程

### 阶段 0 确认范围与偏好

1. 与用户确认仓库地址或本地路径。
2. 过一遍偏好。用户可能一次给全,也可能只说改动的部分。下面这张表是所有可配置项与默认值,没提到的项用默认,不用逐个问。

| 配置项 | 默认 | 可选 |
|---|---|---|
| 目标语言 | 中文 | 中文、英文、中英对照 |
| 时间范围 | 全部历史 | 指定年份区间 |
| 篇幅深度 | 完整版 | 完整版、精编版(每章只留代表性提交) |
| 叙事重点 | 均衡 | 技术架构、社区故事、人物传记、均衡 |
| 结构模板 | 完整 | 完整、精简(去掉论坛回声与附录) |
| 提交粒度 | 逐条 | 逐条、按批次 |
| 数据源 | 全部六类 | 全部、仅 git 提交、指定类别 |
| Mermaid 配图 | 开 | 开、关 |
| 插图风格 | 手绘编年史风 | 用户自定描述(如水墨、版画、赛博) |
| 插图数量 | 封面加关键章节 | 仅封面、每章一张 |
| 作者署名 | 保留 | 保留、匿名化 |
| 产物署名 footer | 保留 | 保留、去掉(powered by 链接) |
| 输出格式 | Markdown | Markdown、Markdown 加 EPUB(电子书)、Markdown 加在线书、Markdown 加 HTML |
| 输出路径 | 仓库 docs/notes/ | 用户指定 |

用户可以直接贴一段偏好,例如下面这样,没提到的项自动用默认。

```
语言 英文,重点 社区故事,插图 水墨风 仅封面
```

2b. 确认产物 footer。用户没提时,主动问一句"文末保留 powered by git-repo-chronicle 的链接吗,默认保留",按回答在阶段 3 决定加不加。

3. 克隆仓库到临时目录,命令是 `git clone --quiet <url> /tmp/<repo>-chronicle`;本地路径直接使用。提交历史巨大(预估数万条)时,直接克隆会超时,改用 `git clone --filter=blob:none --no-checkout`,只拉提交历史、不拉文件内容,编年史不需要 blob。
4. 粗查规模,看 `git log --oneline | wc -l` 与首末提交日期。提交数超过 5000(用户可改阈值)时采用抽样策略(见 `references/data-sources.md`「大仓库策略」),并在文末方法论中标注口径。

### 阶段 1 数据采集(六类来源)

按用户偏好的数据源范围裁剪。选"仅 git 提交"时跳过 2 到 6,省去检索时间。

1. **git 提交**(最核心)。运行 `scripts/dump_git_history.sh <仓库路径> <输出目录>`,得到 `commits.tsv`、`per_year.tsv`、`per_author.tsv`、`commits_full.log`。检查合并提交,从提交消息中提取 PR 编号(`#N`),年份以合入日期为准。
2. **release / tag**。运行 `scripts/fetch_github_meta.sh <owner/repo> <输出目录>`(依赖 gh);本地克隆用 `git tag -l --sort=creatordate --format='%(refname:short) %(creatordate:iso-strict)'` 兜底。
3. **issue / PR**。用 `gh issue list --state all`、`gh pr list --state all`(含 `mergedAt`)拉取;关键 issue 用 `gh issue view <n>` 读正文与讨论。未装 gh 时用 GitHub API 分页拉取。
4. **论坛讨论**。先定位项目官方论坛,看 README 里的链接、官网 footer,或搜索"项目名 forum";老项目常见于垂直社区,如传奇私服的 LOMCN。抓取相关帖的标题、作者、日期、回复数与浏览数;关键帖读正文,必要时用镜像站或存档站交叉验证。
5. **RSS**。GitHub 自带 `https://github.com/<owner>/<repo>/releases.atom` 与 `commits/<branch>.atom`,能快速拿到发布时间线;项目博客、官方通告的 RSS 优先。
6. **新闻与时代背景**。对每个活跃年份,搜索「项目名 + 年份」以及技术栈当年大事(某框架版本发布、平台政策变化、行业风向),用来解释提交背后的动机。检索时用年份限定关键词,防止拿到近期结果。

### 阶段 2 归纳与互证

1. 按年份聚合提交,统计每年的提交数与作者数,绘制 ASCII 条形图。
2. 识别重大事件,如架构迁移、跨平台、重写、发布、fork、停更与复活、社区里程碑。
3. 找出"互文时刻"。社区先有呼声(高回复帖)、代码后落地(对应提交),或代码先行、社区随后跟进,这是编年史最有价值的部分。
4. 建立人物图鉴。记录每位作者的提交数、活跃期、角色定位;用邮箱域名、时区偏移、论坛署名交叉推断身份,未证实的标注「[推断:…未证实]」。

### 阶段 3 写作

严格按 `references/chronicle-structure.md` 的结构模板写作。

- 题头。写日期、数据来源(如"488 条 git 提交逐一核对")、一句核心结论(结论先行)。
- §0 项目是什么。写背景、全景数字表、年度提交量 ASCII 条形图。
- §1 人物图鉴。写作者表格(提交数、活跃期、角色定位)。
- 按年章节。每章以一句"一句话"概括,中间按事件批次罗列提交,结尾"本章关键词"三到五个。
- 每条提交固定一行模板,格式如下。
  ```markdown
  `哈希前7位` **#PR号 标题**(作者)+ 一句话说明该提交做了什么、为什么
  ```
- §10 尾声。写三到五条经验总结(个人与团队、架构复利、社区价值、技术栈跟随时代、项目定位)。
- §11 论坛回声。写与 git 主线并行的社区史,包含热度对照表与互文时刻。
- 附录。写 PR 时间线(★ 标重大事件)、本地 fork 提交清单、论坛数据。
- 配图。按 `references/diagrams.md` 的规范配 Mermaid 图,默认 timeline 和 flowchart。§0 画生命周期 timeline,架构转型章画迁移前后对比,里程碑章画架构快照,§11 画互文时刻流程。图里数字与正文一致。
- 插图(可选)。用户提供了生图配置(ILLUSTRATION_BASE_URL、ILLUSTRATION_API_KEY、ILLUSTRATION_MODEL)时,按 `references/illustrations.md` 生成插图。风格用用户指定的描述,没指定就用默认的手绘编年史风,统一放 `docs/notes/images/` 并嵌入对应章节。缺配置或生成失败就跳过,不阻塞交稿,在回复里说明原因。
- 出版。用户选了 EPUB 或在线书输出时,按 `references/publishing.md` 转成出版物。有生图配置就先生成 3 比 4 封面,再转格式。在线书优先用 VitePress 框架主题(侧边栏目录、本地搜索、深色模式),没有 node 环境时退回 `scripts/md2epub.py --site` 的零依赖静态站。
- 文末。写数据方法论注记(口径、推断、覆盖率)。
- 产物 footer。用户选择保留时,文末加一行分隔线和署名:`---` 换行后写"本文由 [git-repo-chronicle](https://github.com/tsonglew/git-repo-chronicle) 生成"。用户选择去掉时不加。footer 加在 md 源稿文末,EPUB 与在线书转换时自动带上。

写作风格要求是双线并行不混写、微观提交与宏观判断结合、每条论断可溯源(提交哈希 / issue 编号 / URL)、未证实推断显式标注且绝不编造、戏剧化叙事可用但必须以事实为骨。

### 阶段 4 校验

1. 统计核对。文中数字与 `per_year.tsv`、`per_author.tsv` 一致。
2. 溯源抽查。随机抽 10 条提交行,确认哈希、作者、日期与 `commits.tsv` 一致。
3. 附录完整性。PR 时间线覆盖所有带编号的提交;论坛数据附录含年份分布与热门帖 TOP N。
4. 确认所有推断都有标注;成品保存到阶段 0 约定的路径,并在回复中给出文件路径与全文概述。
5. 配图核对。每张图与正文数据一致,每条连线在正文里有对应陈述,Mermaid 语法能在 GitHub 渲染。
6. 插图检查。插了图的,确认图片文件存在、Markdown 引用路径正确、全篇风格一致(手绘编年史风)。
7. 出版校验。出了 EPUB 的,按 `references/publishing.md` 的校验清单过一遍,结构、元数据、目录、图片都要对。
8. 发布审计。成品要推送到公开仓库时,推送前扫一遍,查真实的 API key(`sk-` 开头长串)、内网域名与 IP、本地绝对路径、临时文件(.tgz/.log/.env/mock),git 历史也要查(`git log --all -p | grep` 关键词)。命中就清理后再推,不要带病上线。

## 大仓库与无权限场景

- 无法克隆或只读时,用 GitHub API 分页获取,地址是 `https://api.github.com/repos/<owner>/<repo>/commits?per_page=100`(未认证 60 次/小时,认证后 5000 次/小时)。
- 提交数巨大时,只精读里程碑、release 前后的提交,中间用月度聚合,并在方法论中标注。
- 论坛抓取受限时,改用站点搜索、存档站、Wayback Machine,并在附录注明覆盖率。

## 附加资源

### Reference Files

- **`references/chronicle-structure.md`** 编年史结构模板与写作风格,从章节骨架到动机链,含题头、全景数字表、人物图鉴、按年章节、提交行模板、论坛回声与附录。
- **`references/data-sources.md`** 六类数据源采集手册,命令、实战坑与大仓库策略,含 git 提交、release/issue/PR、论坛、RSS、新闻与身份比对。
- **`references/diagrams.md`** 配图规范,Mermaid 图类型、写法示例、导出与校验。
- **`references/illustrations.md`** 插图规范,风格前缀、模型探测、批量流水线与失败降级。
- **`references/publishing.md`** 出版规范,EPUB 与在线书(框架主题优先)、封面、Mermaid 预渲染与校验清单。

### Scripts

- **`scripts/dump_git_history.sh`** 导出 git 提交为 TSV,并生成年度与作者统计。
- **`scripts/fetch_github_meta.sh`** 用 gh 拉取 release、issue、PR 元数据,无 gh 时给出 API 兜底提示。
- **`scripts/generate_illustration.sh`** 调用生图 API 生成手绘风插图,支持 url 与 b64_json 两种响应。
- **`scripts/md2epub.py`** 把编年史 Markdown 转成 EPUB 3 电子书与在线书站点,纯 Python 标准库,零依赖,支持封面、目录与 Mermaid(EPUB 预渲染,在线书浏览器端渲染)。

### Examples

- **`examples/chronicle-excerpt.md`** 编年史片段示例(虚构项目),含题头、章节、提交行、论坛回声与附录的完整格式示范。
