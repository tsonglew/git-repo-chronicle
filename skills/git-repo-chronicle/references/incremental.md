# 增量续写与截点

已有编年史时，先读旧稿和截点，只补上次截点之后的材料。续写保持旧章的口吻、章节编号和已有来源，追加新一年、新 release 的章节或带日期的「近况」。发现旧章错误时追加「勘误」，注明旧结论、修正、依据与日期；不要顺手重写旧正文、题头统计或旧结论。全书重编是另一个明确的任务。

## 截点文件

`scripts/chronicle_checkpoint.py` 使用 Python 3.8+ 标准库和 Git，不调用网络或模型。它把已审核的 Markdown 当作不可变前缀，记录 `chronicle-checkpoint.json`。截点应与正文一起保存；不要修改哈希字段来绕过校验。

| 字段 | 含义 |
|---|---|
| `version` | 格式版本，目前为 `1` |
| `repository.origin`、`repository.roots` | 归一化的 origin 和初稿历史的根提交；允许换克隆目录，阻止误用其他仓库 |
| `commit` | 初稿已覆盖的完整提交哈希；增量提交范围为 `commit..目标提交` |
| `through` | 本次材料的时间截点，带时区 ISO 8601；与提交图截点分别记录 |
| `source_through.releases`、`.community` | 两类外部来源各自已经完整覆盖到的时间 |
| `source_seen` | 来源不完整时，已引用的新记录标识；补采时用于去重，完整覆盖后清空 |
| `document.path`、`.sha256`、`.bytes` | 正文相对截点文件的路径、SHA-256 和字节数 |
| `last_batch` | 最近一次成功追加的材料批次，用于重复执行时直接跳过 |

初稿应在完整覆盖某个提交和明确日期后初始化。`--commit` 不填时取当前 `HEAD`；不要对只覆盖早期历史的旧稿直接使用最新 `HEAD`。只有日期、没有已核实提交截点的旧稿，先查清原稿实际覆盖到哪次提交，再初始化；提交日期不能可靠推断祖先范围。

以下命令从本 skill 的目录运行，路径替换为实际位置。`--through` 表示你已经核查到的材料边界，不是命令运行时间。

```bash
python3 scripts/chronicle_checkpoint.py init \
  --repo /path/to/repo \
  --document /path/to/notes/chronicle.md \
  --checkpoint /path/to/notes/chronicle-checkpoint.json \
  --commit HEAD \
  --through 2026-08-14T23:59:59+08:00
```

`init` 拒绝覆盖已有截点。首次建截点前，核实旧稿对两类外部来源已覆盖到 `--through`，不要把「未获取」当成完成覆盖；历史缺口保留在方法论中，后续需专门补采并以勘误说明。

## 采集新增材料

1. 固定本次目标提交和时间。Git 用祖先范围采集，不用 `--since` 切掉日期较早、后来才合入的提交。目标必须包含原截点；rebase 或强推导致历史分叉时停止自动续写，人工核对后另建版本。
2. release、论坛、RSS、新闻在采集端按各自 `source_through < published_at <= 本次 through` 限定检索，保留实际发布时间、URL 和原始证据。可把来源工具返回的完整数组交给脚本再次过滤；本脚本本身不下载来源。
3. 用独立目录保留新材料，`collect` 只生成批次，不修改正文和截点。

```bash
python3 scripts/chronicle_checkpoint.py collect \
  --repo /path/to/repo \
  --checkpoint /path/to/notes/chronicle-checkpoint.json \
  --to HEAD \
  --through 2026-10-22T18:00:00+08:00 \
  --releases /path/to/recent-releases.json \
  --community /path/to/community-records.json \
  --out /path/to/notes/batches/2026-10-22
```

输入格式如下。

- `--releases` 是 JSON 数组，兼容 `fetch_github_meta.sh` 的 `tagName`、`publishedAt`，也兼容 GitHub API 的 `tag_name`、`published_at`。输入必须覆盖检索区间的所有分页，不能把工具默认 limit 返回的截断列表视作完整；无法证明完整时加入 `{"status":"unavailable","reason":"分页未完成"}` 以保留缺口。
- `--community` 是 JSON 数组，见 [`examples/community-records.json`](../examples/community-records.json)。成功记录的 `status` 为 `ok`（省略时也视作 `ok`），必须有 `url` 和带时区的 `published_at`；正文引用还必须能回到实际内容，采集规则见 [`data-sources.md`](data-sources.md)。
- 失败记录使用 `status: "unavailable"` 和具体 `reason`，允许 `url`、`published_at` 为 `null`。输出到 `community-gaps.json` 或 `releases-gaps.json`，不当成社区反应或新 release。
- 时间缺失或非法的成功记录会报错。先核实日期，核实不了就标为 `unavailable`，不要使用抓取时间冒充发布时间。
- 没有提供某类输入时，输出「未提供数据」缺口，该类来源水位保持不变。空数组 `[]` 表示确实已完整查询且没有新记录，只有确认覆盖完整时才使用。

只要一类来源存在缺口，其日期水位就不前移；已经写过的成功记录会记入 `source_seen`，下次补采时不会重复出现。来源标识由 URL（release 使用 id/tag）和发布时间构成，同一 URL 的内容编辑不算新事件；需要更正旧结论时走勘误流程。

批次包含 `commits.tsv`、`commits_full.log`、`per_year.tsv`、`per_month.tsv`、`per_author.tsv`、过滤后的 `releases.json` / `community.json`、两份缺口 JSON，以及记录校验和的 `batch.json`。TSV 的日期使用 Git committer date（`%cI`），与全量导出一致；这不是严格的 PR `mergedAt`。作者使用原始 `%an/%ae`，按邮箱统计活跃作者；`.mailmap` 归并应另行核实并保留映射，避免全量和增量口径漂移。统计仅代表本次新增范围，不能拿它替换原稿的全年统计。release 数与 tag 数不是同一概念，增量批次没有生成 `tags.tsv`，需要 tag 数时另行核查。

## 审阅并追加

把新材料写成独立的 `new-chapter.md`，以 `## ` 二级标题开始。延续旧稿文风，不把旧章复制过来。新章标明本次提交范围、来源区间、采集缺口；没有新提交但有新 release 或社区证据时，可以追加「近况」。每项结论仍需来源和时光机锚点。

旧三幕梗概、人物表、统计和目录都属于已发布正文，继续保留原文；新截点、增量统计、贡献者变化在追加部分另写。材料足够写完整新章时使用标准章节模板；只有一条提交或零星材料时用简短「近况」，勘误也按修正内容组织。这两类小节不必凑两批事件，不重复全书梗概与人物图鉴。重新生成 EPUB 或在线书时可在出版阶段重建导航，Markdown 旧正文保持不变。

```bash
python3 scripts/chronicle_checkpoint.py append \
  --repo /path/to/repo \
  --checkpoint /path/to/notes/chronicle-checkpoint.json \
  --batch /path/to/notes/batches/2026-10-22/batch.json \
  --chapter /path/to/notes/new-chapter.md
```

脚本校验旧稿、仓库身份、提交祖先关系、批次和材料校验和，然后将新增 Markdown 追加到旧文件的最后一个字节之后，再推进截点。旧稿被编辑、批次过期、材料被改动时均报错。相同批次重复执行不重复写入。写正文成功、更新截点失败时，可使用相同批次和相同新章重跑恢复；不要删除截点或手动重复粘贴。

同一正文只运行一个追加进程。两个文件不能跨文件原子替换，本脚本提供上述中断恢复，但不提供并发写锁。新章的事实正确性、引用覆盖率和文风仍需写作阶段人工或代理审核，校验和只保证已有正文和已采集文件未变。

没有任何新材料时拒绝追加空章，也不推进截点。确有更正可准备以 `## 勘误` 开头的 Markdown，并在同一 `append` 命令末尾加 `--erratum`；勘误写明依据，旧正文继续保留。

## 回归验证

从项目根目录执行：

```bash
python3 -m unittest discover -s tests -p test_incremental.py -v
```

测试会创建小型临时 Git 仓库，完成初稿、两轮续写，逐字节确认第一章不变；还覆盖重复执行、committer/author 日期不同、来源区间边界、缺口补采去重、旧稿或材料被修改、过期批次、历史分叉，以及正文写入后截点更新中断的恢复。
