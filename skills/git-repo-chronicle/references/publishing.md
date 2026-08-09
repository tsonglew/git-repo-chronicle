# 电子出版物规范

编年史的最终产物以电子出版物为标准。源稿始终是 Markdown,出版物从源稿转换而来,保证改一处、重转一次即可。

## 目标格式

| 格式 | 定位 | 工具 |
|---|---|---|
| EPUB 3 | 默认出版物,微信读书、Apple Books、Kindle(经 Calibre 转换)可读 | scripts/md2epub.py,纯 Python 标准库,零依赖 |
| 在线书(HTML 站点) | 网页版,目录页加分章页,扔静态托管即上线 | 同脚本的 --site 模式 |
| PDF | 可选,需要 pandoc 加 xelatex,不默认 | pandoc --pdf-engine=xelatex |

## 转换命令

```bash
python3 scripts/md2epub.py <编年史.md> <输出.epub> [--site 在线书目录] [--cover 封面.png] [--author 作者名]
```

- 加 `--site` 时,同一份源稿额外生成在线书目录,含index.html 目录页、chapters/ 分章页、styles.css、images/。
- 标题自动取文档第一个 `#` 标题。
- 作者用 `--author` 指定,没指定用 git 用户。
- 语言固定 zh,日期取文档里的"整理日期",没有则用当天。
- 目录按二级标题自动生成,阅读器可跳转。

## 在线书

在线书跑在浏览器里,可以执行 JavaScript,所以 Mermaid 图由 mermaid.js 在浏览器实时渲染(章节页引用 jsdelivr CDN),不需要预渲染,这是它与 EPUB 最大的区别。EPUB 的 Mermaid 才需要 mmdc 或 kroki 预渲染。

部署方式任选。

- 本地阅读,双击 index.html。
- 上线,把 site/ 目录推到 GitHub Pages、Vercel 或任意静态托管,配一个域名或子路径。
- 章节页引用了 CDN,离线打开时 Mermaid 不渲染但源码块可见;要完全离线,把 mermaid.min.js 下载到 site/ 下改成本地引用。

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
