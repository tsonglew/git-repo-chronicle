# 数据源采集手册

编年史的六类数据源是 git 提交、release/tag、issue/PR、论坛讨论、RSS、新闻与时代背景。按序采集,逐类归档到输出目录,保持文件命名一致,便于阶段 2/3 引用。

## 1. git 提交(最核心)

```bash
# 导出结构化数据(推荐:使用 scripts/dump_git_history.sh)
git log --date=iso-strict --pretty=format:'%H%x09%an%x09%ae%x09%ad%x09%s' > commits.tsv
# 完整日志(含正文,供精读)
git log --date=iso-strict --pretty=format:'commit %H%nAuthor: %an <%ae>%nDate:   %ad%n%n    %s%n%n%b%n%n---' > commits_full.log
```

处理时记住几点。

- **PR 编号提取**。从提交消息中提取 `#N`,排除误匹配(如 "C# 语法" 里的 #)。规则是优先匹配独立的 `#数字` 词元;合并提交(merge commit)是主要来源,用 `git log --merges` 单独列出核对。
- **年份口径**。以合入日期(author/commit 日期)为准,不用提交消息里的日期。
- **时区**。ISO 日期自带偏移(`+0800` 即中国时区),用来推断作者地域。
- **定位特定功能引入**。用 `git log -S'关键字' --oneline`(字符串变更)或 `git log --grep'关键词'`;单文件历史用 `git log --follow -- <path>`。
- **主线过滤**。`git log --first-parent` 只保留主分支合入,适合噪音大的仓库。

## 2. release / tag

```bash
# 本地克隆(始终可用)
git tag -l --sort=creatordate --format='%(refname:short)%x09%(creatordate:iso-strict)%x09%(subject)'
# gh(推荐,含正文)
gh release list --repo <owner/repo> --limit 200 --json tagName,publishedAt,name,body
```

## 3. issue / PR

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
- 实战坑三,PR 不在本仓库。fork 仓库可能查不到上游 PR(gh pr list 为空)。此时从提交消息提取 `#N` 编号重建 PR 时间线:`grep -oE '#[0-9]{2,4}' commits.tsv | sort -u`,按首次出现的年份归入附录 A,编号池跨仓库迁移时在方法论中注明。
- 多语言 issue(韩语、西语、中文等)本身就是社区全球化的证据,翻译后引用,并在原文旁标注语言。
- 历史 issue 的讨论串是"社区呼声"的直接证据,标注 `#编号` 供附录速查。

## 4. 论坛讨论

定位路径按下面的顺序试。

1. 项目 README / 官网 footer 的论坛链接。
2. 搜索「项目名 forum」,老项目常落在垂直社区(如 LOMCN 之于传奇私服)。
3. 搜索「项目名 发布 讨论」找发布帖。

抓取字段(逐帖)有标题、作者、日期、回复数、浏览数、链接。关键帖(高回复、涉及方向争议、涉及作者身份)读取正文。

- 分页抓全。记录总页数与帖子数,附录中写明覆盖率。
- 交叉验证。关键帖正文用镜像站(如 lomdn.com)、存档站或 Wayback Machine 二次确认。
- 抓取受限时。用 `site:<论坛域名> <项目名>` 的站点搜索代替,并注明覆盖率不足。

## 5. RSS

GitHub 自带 feed,无需第三方。

- release `https://github.com/<owner>/<repo>/releases.atom`
- commits `https://github.com/<owner>/<repo>/commits/<branch>.atom`
- issues `https://github.com/<owner>/<repo>/issues.atom`(可能要求登录)

项目博客、官方通告、维护者个人站的 RSS 优先于新闻聚合。RSS 的用途是拿到精确的发布时间线,与 git 提交日期互证。

## 6. 新闻与时代背景

对每个活跃年份做两到三次检索,按下面的组合试。

1. 「<项目名> <年份>」,查项目当年的新闻与版本动静。
2. 「<项目名> 发布 / 更新 <年份>」,查发布节点。
3. 「<技术栈> <年份> 大事件」,查技术背景,例如「.NET Core 2020 发布」「Godot 4.0 2023」「WebAssembly 2019」。
4. 平台/政策,如「Steam 抽成政策 2018」「苹果税」,查影响项目定位的外部事件。

搜索引擎默认给近期结果,必须用年份限定关键词;引用的新闻标注来源 URL。

## 身份比对方法

把 git 作者与论坛/issue 里的身份对上,这是人物图鉴的关键。

- **邮箱域名**。`development@suprcode.com` 这类域名证明作者与某站、某项目同属一人或一团队。
- **时区偏移**。提交日期偏移 +0800 推断中国时区开发者;跨多年偏移稳定者是常驻作者。
- **署名昵称**。论坛 ID 与 git 作者名相近(如论坛 "AndyF" 与提交者 "AndyF")。
- **committer 与 author**。两者不同时,说明代码被人代为合入,可推测协作关系。
- 所有推断标注「[推断:…未证实]」,写明依据;无法对上的身份归入"匿名贡献者"。

## 大仓库策略(超过 5000 条提交)

- 克隆阶段就用 blob 过滤,避免克隆超时。`git clone --filter=blob:none --no-checkout <url>` 只拉提交历史与目录树,文件内容按需下载,编年史写作不需要 blob。
- 主线优先。`git log --first-parent` 砍掉分支噪音。
- 窗口精读。以 release/tag 为中心,精读每个里程碑前后约 30 天的提交;窗口之间用月度聚合(`git log --date=format:'%Y-%m'` 统计)一笔带过。
- 月度代表性提交。按月取前几条 merge 提交做窗口素材,命令是 `git log --first-parent --merges --date=format:'%Y-%m' --pretty=format:'%ad %s' | grep '^2026-05'`,只挑与当月主题相关的展开,其余当背景。
- 明确口径。方法论注记中写明"仅精读 N 个里程碑窗口,其余按月聚合"。
- release 列表(gh 或 tags)在超大仓库里比提交列表更能代表"官方叙事",让 release 成为章节骨架。

## 检索与推断的防错规则

1. 绝不编造。拿不到的数据宁可不写,也不补一个"合理"的日期或回复数。
2. 一切数字可回溯。正文出现任何统计,先核对 `per_year.tsv`、`per_author.tsv` 或抓取文件。
3. 推断降级。身份、动机、因果关系,证据不足一律标注或降级为"可能的解释"。
4. 时代背景只做背景。新闻用于解释"为什么",不替代项目自身事实。
