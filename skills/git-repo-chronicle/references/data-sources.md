> 六类数据源的采集手册,git 提交、release/tag、issue/PR、论坛、RSS、新闻。每类给出可复制的命令与已知的坑,大仓库策略、身份比对方法、动机链素材的获取都在本文。

# 数据源采集手册

编年史的六类数据源是 git 提交、release/tag、issue/PR、论坛讨论、RSS、新闻与时代背景。按序采集,逐类归档到输出目录,保持文件命名一致,便于阶段 2/3 引用。

## 最快路径,先跑这三条

数据采集的最小动作。这三条跑完就有了写作所需的全部统计数字,后面几类是补充。

```bash
# 1. 克隆(大仓库加 --filter=blob:none --no-checkout 防超时)
git clone --quiet <url> /tmp/<repo>-chronicle

# 2. 导出提交与统计,产出 commits.tsv、per_year.tsv、per_month.tsv、per_author.tsv、tags.tsv
bash scripts/dump_git_history.sh /tmp/<repo>-chronicle /tmp/<repo>-meta

# 3. 拉 GitHub 元数据,产出 releases.json、issues.json、prs.json、pr_issue_links.tsv
bash scripts/fetch_github_meta.sh <owner/repo> /tmp/<repo>-meta
```

跑完先看这几个数,它们决定章节怎么分。

```bash
cat /tmp/<repo>-meta/meta.txt          # 总提交数、首末提交、tag 数
cat /tmp/<repo>-meta/per_month.tsv     # 月份 | 提交数 | 作者数,决定按月还是按年分章
head -10 /tmp/<repo>-meta/per_author.tsv  # 谁是核心作者
```

分章规则很简单。项目跨多年就按年分章;项目只有几个月但提交密集(如单月上千条)就按月分章;某几个月提交量都很低,合成一章并在标题里写明"X 到 Y 月合计 N 条"。

## 1. git 提交(最核心)

> 先跑 scripts/dump_git_history.sh <仓库> <输出目录>,得 commits.tsv 与月度/作者统计

```bash
# 导出结构化数据(推荐:使用 scripts/dump_git_history.sh)
git log --pretty=format:'%H%x09%an%x09%ae%x09%cI%x09%s' > commits.tsv
# 完整日志(含正文,供精读)
git log --pretty=format:'commit %H%nAuthor: %an <%ae>%nCommitDate: %cI%n%n    %s%n%n%b%n%n---' > commits_full.log
```

处理时记住几点。

- **PR 编号提取**。从提交消息中提取 `#N`,排除误匹配(如 "C# 语法" 里的 #)。规则是优先匹配独立的 `#数字` 词元;合并提交(merge commit)是主要来源,用 `git log --merges` 单独列出核对。
- **年份口径**。导出和年度/月度统计统一采用 committer 日期 `%cI` 的原时区年月。它不是 author 日期 `%aI`，也不必然等于 PR 合入时间；需要主线合入节奏时使用 `--first-parent`，或独立按 PR `mergedAt` 作图并明确标注，不能混算。
- **时区**。ISO 日期保留原偏移（如 `+08:00`）；它不能证明作者所在地或国籍，身份推断须有其他来源。
- **定位特定功能引入**。用 `git log -S'关键字' --oneline`(字符串变更)或 `git log --grep'关键词'`;单文件历史用 `git log --follow -- <path>`。
- **主线过滤**。`git log --first-parent` 只保留主分支合入,适合噪音大的仓库。

## 2. release / tag

> 先跑 git tag -l --sort=creatordate,或 scripts/fetch_github_meta.sh(含 release 正文)

```bash
# 本地克隆(始终可用)
git tag -l --sort=creatordate --format='%(refname:short)%x09%(creatordate:iso-strict)%x09%(subject)'
# gh(推荐,含正文)
gh release list --repo <owner/repo> --limit 200 --json tagName,publishedAt,name,body
```

## 3. issue / PR

> 先跑 scripts/fetch_github_meta.sh <owner/repo> <输出>,prs.json 含 body(动机链素材)、pr_issue_links.tsv(Closes 关联)

```bash
gh issue list --repo <owner/repo> --state all --limit 500 \
  --json number,title,createdAt,closedAt,state,labels
gh pr list --repo <owner/repo> --state all --limit 500 \
  --json number,title,mergedAt,createdAt,state,labels
gh issue view <n> --repo <owner/repo>   # 关键 issue 的正文与评论
```

- 无 gh 时改用 API 拉取,`curl -s "https://api.github.com/repos/<owner>/<repo>/issues?state=all&per_page=100&page=N"`,分页直到返回空数组。速率限制是未认证 60 次/小时,`gh auth` 或 `GITHUB_TOKEN` 后 5000 次/小时。
- 实战坑一,release 字段差异。部分实例的 release 没有 body 字段,`--json body` 会报 Unknown JSON field,去掉该字段即可。fetch_github_meta.sh 已按此处理。
- 实战坑二,issue 被禁用。仓库在设置里关掉 issues 后,gh 报 "disabled issues",issues.json 为空,属正常,不是抓取失败。
- 实战坑三,PR 不在本仓库。fork 仓库可能查不到上游 PR(gh pr list 为空)。此时从提交消息提取 `#N` 编号重建 PR 时间线,命令是 `grep -oE '#[0-9]{2,4}' commits.tsv | sort -u`,按首次出现的年份归入附录 A,编号池跨仓库迁移时在方法论中注明。
- 多语言 issue(韩语、西语、中文等)本身就是社区全球化的证据,翻译后引用,并在原文旁标注语言。
- 历史 issue 的讨论串是"社区呼声"的直接证据,标注 `#编号` 供附录速查。

## 4. 论坛讨论

> 先读项目的社区来源配置；没有配置时再看 README、官网 footer 或搜索「项目名 forum」。

### 项目级来源清单

复制 [community-sources.json](../examples/community-sources.json) 到产物目录，填入已核实的论坛、Reddit、Hacker News、发行说明和博客 RSS URL。示例针对本仓库，仅填写可由仓库地址直接确定的 GitHub 地址；未知平台保留 `url: null` 和 `enabled: false`，不能把示例当成已发现的社区。配置是采集清单，由代理或所选采集工具读取，本项目不内置通用论坛爬虫。

每项保留稳定 `id`、`kind`、`url`、`enabled` 与 `notes`。URL 是发现入口，不是论断证据。搜索页、RSS 首页或论坛首页只能帮助定位，最终引用须指向具体帖、评论、发行说明或文章。用户没有选中的来源可禁用，并在方法论写「未纳入」；希望采集但缺地址、权限或正文时写「未获取」。首次发现新的来源时补回清单，下次续写按同一清单复查。

采集逐条记录到 `community.json`（JSON 数组），字段如下。可从 [记录模板](../examples/community-records.json) 开始，模板中的未获取项不能当作真实采集结果。

| 字段 | 约定 |
|---|---|
| `source_id` | 对应配置项的 `id` |
| `url`、`title` | 具体内容的固定链接与标题；未定位到内容时 URL 可为入口或 null |
| `published_at` | 内容本身发布时间，带时区 ISO 8601；不能用抓取日或 Wayback 存档日代替 |
| `fetched_at` | 实际读取时间，带时区 ISO 8601 |
| `status` | `ok` 表示读到可核对正文；`unavailable` 表示未获取 |
| `excerpt` | 支撑论断的短摘录或明确标注的摘要，并注明作者/评论位置；注意保留语境 |
| `reason` | 未获取原因，如未配置地址、登录限制、HTTP 404、正文被删、无可用存档 |
| `snapshot_url` | 可选，实际打开并核对过的快照 URL |

只看搜索摘要、标题或一个高回复数，不能据此写「社区普遍欢迎」「引发反对」或归因开发动机。`status=ok` 的内容必须有来源、可核对正文和已确认的发布时间；日期或正文缺失时先标为 `unavailable`，并说明到底缺什么。一个用户的评论只能说明该用户的观点。

增量采集使用 `published_at`，和 `chronicle_checkpoint.py collect --community community.json` 的输入一致。`unavailable` 项写入 `community-gaps.json`，不作为社区反应证据；有缺口时保留旧的社区时间水位，恢复后才能补采。日期非法的 `ok` 项会导致校验失败，先核实或降级后重跑。旧帖的新评论按评论自身时间建独立记录，不能把整帖的抓取日期当新事件。

### 缺口降级与快照

先试原链接，再按需要尝试站内搜索、镜像或 Wayback；记录尝试过的入口和失败原因，无法获取即停止补写。禁止用模型自行补齐社区反应。

可直接采用以下文案，尖括号替换为实际情况：

> 社区资料未获取。来源为 <平台/URL>，尝试于 <时间>，原因为 <具体错误或缺失字段>，覆盖缺口为 <日期/话题范围>。本章仅依据已核实的代码与发行记录，不据此判断社区态度。

> 已获取 <N> 条可核对来源，范围为 <日期区间>；<来源/页码> 未获取，原因为 <原因>。下文观点仅对应所引用的作者或帖子，不能代表整个社区。

Wayback 发现入口可写 `https://web.archive.org/web/*/<原始URL>`，但通配入口不是证据。真正引用时记录实际快照地址 `https://web.archive.org/web/<快照时间>/<原始URL>`、原始 URL、原文发布日期和存档时间；删除帖只有摘要缓存而无正文时仍标未获取。存档时间不能代替原帖时间，也不能据此推导当时的回复数。

交付前逐句检查所有社区反应与因果判断：有可核对的内容链接和对应记录，或在该处明确写「未获取」并移除无证据判断。文末同时列出来源清单、已获取范围和缺口，空数组只代表无记录，不代表社区没有发声。

### 发现与读取帖子

定位路径按下面的顺序试。

1. 项目 README / 官网 footer 的论坛链接。
2. 搜索「项目名 forum」,老项目常落在垂直社区(如 LOMCN 之于传奇私服)。
3. 搜索「项目名 发布 讨论」找发布帖。

抓取字段(逐帖)有标题、作者、日期、回复数、浏览数、链接。关键帖(高回复、涉及方向争议、涉及作者身份)读取正文。

- 分页抓全。记录总页数与帖子数,附录中写明覆盖率。
- 交叉验证。关键帖正文用镜像站(如 lomdn.com)、存档站或 Wayback Machine 二次确认。
- 抓取受限时。用 `site:<论坛域名> <项目名>` 的站点搜索代替,并注明覆盖率不足。

## 5. RSS

> 先看 https://github.com/<owner>/<repo>/releases.atom,先拿 release 时间线

GitHub 自带 feed,无需第三方。

- release `https://github.com/<owner>/<repo>/releases.atom`
- commits `https://github.com/<owner>/<repo>/commits/<branch>.atom`
- issues `https://github.com/<owner>/<repo>/issues.atom`(可能要求登录)

项目博客、官方通告、维护者个人站的 RSS 优先于新闻聚合。RSS 的用途是拿到精确的发布时间线,与 git 提交日期互证。

## 6. 新闻与时代背景

> 先搜 WebSearch「项目名 + 年份」,逐年限定关键词

对每个活跃年份做两到三次检索,按下面的组合试。

1. 「<项目名> <年份>」,查项目当年的新闻与版本动静。
2. 「<项目名> 发布 / 更新 <年份>」,查发布节点。
3. 「<技术栈> <年份> 大事件」,查技术背景,例如「.NET Core 2020 发布」「Godot 4.0 2023」「WebAssembly 2019」。
4. 平台/政策,如「Steam 抽成政策 2018」「苹果税」,查影响项目定位的外部事件。

搜索引擎默认给近期结果,必须用年份限定关键词;引用的新闻标注来源 URL。

## 身份比对方法

把 git 作者与论坛/issue 里的身份对上,这是人物图鉴的关键。

- **邮箱域名**。共享邮箱域名只能提供关联线索，不能证明两条署名属于同一人或同一团队。优先采用项目维护的 `.mailmap` 或作者本人确认的关联。
- **时区偏移**。提交日期偏移只说明当次记录使用的时区，不能单独判断国籍、所在地或是否常驻；相同偏移不等于同一作者。
- **署名昵称**。论坛 ID 与 git 作者名相近(如论坛 "AndyF" 与提交者 "AndyF")。
- **committer 与 author**。两者不同时可能是代为合入、机器人操作或历史重写，须结合提交说明和 PR 记录核对，不能仅凭字段推导协作关系。
- 所有推断标注「[推断:…未证实]」,写明依据;无法对上的身份归入"匿名贡献者"。

## 大仓库策略(超过 5000 条提交)

- 克隆阶段可用 blob 过滤，减少初次传输。`git clone --filter=blob:none --no-checkout <url>` 先取得提交历史与目录树；日志统计无需 blob，核对行为变更、历史文件锚点和代码存活时再按需下载文件内容，并记录缺失或下载失败。
- 主线优先。`git log --first-parent` 砍掉分支噪音。
- 窗口精读。以 release/tag 为中心,精读每个里程碑前后约 30 天的提交;窗口之间用月度聚合(`git log --date=format:'%Y-%m'` 统计)一笔带过。
- 月度代表性提交。按月取 merge 提交做窗口素材，命令是 `git log --first-parent --merges --format='%cI %s' | grep '^2026-05'`，按 committer 日期的原时区年月筛选；只挑与当月主题相关的展开，其余当背景。
- 明确口径。方法论注记中写明"仅精读 N 个里程碑窗口,其余按月聚合"。
- release 列表(gh 或 tags)在超大仓库里比提交列表更能代表"官方叙事",让 release 成为章节骨架。

## 检索与推断的防错规则

1. 绝不编造。拿不到的数据宁可不写,也不补一个"合理"的日期或回复数。
2. 一切数字可回溯。正文出现任何统计,先核对 `per_year.tsv`、`per_author.tsv` 或抓取文件。
3. 推断降级。身份、动机、因果关系,证据不足一律标注或降级为"可能的解释"。
4. 时代背景只做背景。新闻用于解释"为什么",不替代项目自身事实。
