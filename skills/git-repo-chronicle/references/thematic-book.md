> 主题成书模式。当内容不是「某 git 仓库的开发编年史」,而是按主题/区域/条目手写的 Markdown 书(如游戏 Boss 图鉴、指南手册)时读本文。默认仍走 git 编年史;仅用户明确要主题书或无仓库主线可采时启用。

# 主题成书模式 (thematic book)

## 何时用

| 用主题成书 | 仍用 git 编年史 |
|---|---|
| 用户要做 Boss 图鉴、攻略、手册、专题合集 | 用户给了 GitHub/本地仓库并要「项目开发史」 |
| 叙事骨架是大纲/目录,不是 commits | 叙事骨架是提交、release、issue |
| 数字来自作者整理的条目与引用链接 | 数字必须来自 dump_git_history 脚本 |

一句分流:有 git 主线且要编年史 → 默认路径;只有主题大纲、要 EPUB/在线书 → 本文。

**不会做的事:** 不会自动爬 wiki 或游戏 API 填 Boss 正文。条目由用户或作者 Markdown 提供;本 skill 管结构、校验口径与出版。

## 输入

任选一种,或组合:

1. **YAML 大纲** `outline.yaml`(推荐)
2. **Markdown 目录** 带 `##` / `###` 层级
3. **已写好的分章 Markdown** 目录(每文件一章)

YAML 示例:

```yaml
mode: thematic
title: "示例·影之刃零 Boss 札记"
lang: zh
art_style: chinese-wuxia-horror   # 见 illustrations.md 预设表
output:
  markdown: docs/notes/boss-book.md
  epub: true
  site: false
sources_note: "条目来自公开攻略与作者实测;非官方数据。"
chapters:
  - id: region-weeping
    title: 悲泣溪谷
    type: region
    entries:
      - id: can-gang
        title: 痴狂暴徒·残钢
        role: 流程教学
        location: 红丝线障壁之后
        sources:
          - "https://example.com/guide"
  - id: region-lu
    title: 陆家村
    type: region
    entries:
      - id: zhuo-bi
        title: 守门人·拙壁
        role: 游荡
        location: 老根头后再过石桥
```

## 单条(Boss/条目)模板

主题书**不要**套用 git 章的「数据速览 / 事件批次 / 真哈希」铁律。每条用下面结构(可删减空节,不可伪造未写来源):

```markdown
### <条目名>

**位置:** <区域·点位>
**角色:** 主线 / 可选·游荡 / 隐藏 / 章节 Boss
**机制要点:** <1–5 条,可执行>
**配装提示:** <武器/饰品/逃课思路;没有就写「未整理」>
**隐藏条件:** <无则省略整行>
**来源:**
- [<标题>](<url>) — <一句说明>
```

区域章用 `## <区域名>`,章首可放一张插图(风格见预设)。

## 主题书的「铁律」(替代 git 七条)

动笔与交稿前自查:

1. **mode 显式为 thematic**(偏好、大纲或文首 frontmatter `mode: thematic`)。
2. **禁止要求 commits.tsv / 真哈希**;文中不要出现占位哈希。
3. **每条有来源或标明「作者笔记 / 未核实」**;不许假装官方数据。
4. **结构:** 题头 →(可选)总览表 → 按区域/主题分章 → 条目 → 文末方法论(来源覆盖与缺口)。
5. **插图**若开启,必须先选定 `art_style` 预设(或用户全文统一自定义前缀),全篇一致。
6. **出版**仍走 `references/publishing.md`(md2epub / VitePress / `--site`)。
7. **拿不到的攻略写「未获取」**,不编造机制。

## 工作流程(精简)

### 阶段 0

确认 mode=thematic、书名、语言、是否出 EPUB/在线书、`art_style` 预设。不克隆目标「游戏」仓库;若用户另有写作仓,可克隆该写作仓只为落稿。

### 阶段 1 大纲

收集或生成 `outline.yaml` / 目录 Markdown。用户给了 Boss 名单就按区归类;缺名的标「待补」。

### 阶段 2 写作

按条目模板填正文。优先用户提供的笔记;公开攻略只作引用并保留链接。

### 阶段 3 插图(可选)

读 `references/illustrations.md` 的**风格预设**表,取 `chinese-wuxia-horror` 等前缀 + 章节主题,调用 `scripts/generate_illustration.sh`。无配置则跳过。

### 阶段 4 出版

同 `publishing.md`。源稿可以是单文件长 Markdown,或已拆好的 `docs/chapters/`。

### 阶段 5 校验

- [ ] frontmatter / 题头含 mode=thematic 或等价说明
- [ ] 无假 git 哈希、无「本月 X 条提交」速览
- [ ] 每条来源或「未核实」标注齐全
- [ ] 插图路径存在且风格统一
- [ ] EPUB/站点按出版清单抽查

## 与 git 编年史叠用

允许:主题书仓库本身再用默认模式写一部「本书是怎么写出来的」开发编年史(附录或独立成稿)。两套 mode 不要混在同一篇正文里。

## 示例

见 `examples/thematic-boss-book/`。
