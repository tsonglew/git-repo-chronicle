# 电子出版物规范

编年史的最终产物以电子出版物为标准。源稿始终是 Markdown,出版物从源稿转换而来,保证改一处、重转一次即可。

## 目标格式

| 格式 | 定位 | 工具 |
|---|---|---|
| EPUB 3 | 默认出版物,微信读书、Apple Books、Kindle(经 Calibre 转换)可读 | scripts/md2epub.py,纯 Python 标准库,零依赖 |
| 在线书(VitePress) | 推荐形态,成熟框架主题,含侧边栏目录、本地搜索、深色模式、上一章下一章 | VitePress + vitepress-plugin-mermaid |
| 在线书(零依赖) | 备选形态,md2epub.py 的 --site 模式,无 node 环境时用 | 同脚本的 --site 模式 |
| PDF | 可选,需要 pandoc 加 xelatex,不默认 | pandoc --pdf-engine=xelatex |

## 在线书(推荐用 VitePress)

成熟框架主题优先,不要自造样式。VitePress 默认主题自带侧边栏章节目录、本地搜索、深色模式、目录大纲、上一章下一章导航,全部开箱即用。参考实现是 openclaw-chronicle 仓库(https://openclaw-chronicle.vercel.app)。

```bash
# 初始化
npm init -y
npm install vitepress vitepress-plugin-mermaid
# 结构
#   package.json          scripts: docs:build = vitepress build docs
#   vercel.json           framework: vitepress, output: docs/.vitepress/dist
#   docs/.vitepress/config.mts   标题、侧边栏、搜索、mermaid 插件
#   docs/index.md                 首页(封面与核心结论)
#   docs/chapters/chNN.md         按章拆分
#   docs/public/images/           插图与封面
# 构建与部署
npm run docs:build
npx vercel deploy --prod --yes --name <项目名>
```

要点如下。

- 章节按 `##` 拆分到 docs/chapters/,每章一个文件,标题行改成 `#`。
- 图片引用路径改成 `/images/xxx.jpg`(public 根)。
- 侧边栏在 config.mts 里按章节顺序手工列出,保证章节顺序可控。
- Mermaid 用 vitepress-plugin-mermaid,浏览器端渲染,无需预渲染。
- 部署用 Vercel 框架构建(vercel.json 指定 buildCommand 与 outputDirectory),不是静态直传。

## 在线书(零依赖备选)

没有 node 环境时,用 md2epub.py 的 --site 模式,生成自包含静态站,双击 index.html 可读。样式为内置的羊皮纸编年史风,功能少于框架版(无搜索、无侧边栏),但零依赖。

## 转换命令

```bash
python3 scripts/md2epub.py <编年史.md> <输出.epub> [--site 在线书目录] [--cover 封面.png] [--author 作者名]
```

- 加 `--site` 时,同一份源稿额外生成零依赖在线书目录,含 index.html 目录页、chapters/ 分章页、styles.css、images/。
- 标题自动取文档第一个 `#` 标题。
- 作者用 `--author` 指定,没指定用 git 用户。
- 语言固定 zh,日期取文档里的"整理日期",没有则用当天。
- 目录按二级标题自动生成,阅读器可跳转。

## 封面

- 有生图配置时,用 `references/illustrations.md` 的规范生成封面,比例 3 比 4(建议 1024x1365 或 600x800),风格与全书插图一致。
- 用户提供了封面图文件,直接传给 `--cover`。
- 没有封面不报错,电子书照常生成,只是少了封面页。

## Mermaid 图处理

EPUB 阅读器不执行 JavaScript,Mermaid 代码块必须预渲染成图片。转换脚本按顺序尝试。

1. 本机 mmdc(mermaid-cli)。
2. kroki 在线服务(https://kroki.io),需要网络。
3. 都不可用时降级,保留 Mermaid 源码为代码块,并在文末注明"图见源稿"。

## 校验

1. `unzip -l 输出.epub` 看结构,`mimetype` 必须是第一个文件且不压缩。
2. `unzip -p 输出.epub OEBPS/content.opf` 看元数据,标题、作者、语言、日期正确。
3. 目录章节与源稿二级标题一致。
4. 有图片的,确认 `OEBPS/images/` 里有对应文件,正文引用路径正确。
5. 有条件的用 epubcheck 校验,或用阅读器实际打开翻一遍。

## 注意事项

- 转换脚本支持 Markdown 子集,包括标题、段落、列表、表格、代码块、引用、图片、链接、粗体、行内代码。编年史模板用到的都覆盖。
- 转换前先跑一遍 `references/diagrams.md` 的配图校验,保证 Mermaid 语法能渲染,否则电子书里是空图或源码。
- EPUB 是 reflowable,版式由阅读器决定,不要期望像素级排版;要固定版式再走 PDF。
