#!/usr/bin/env python3
"""
md2epub.py — 把编年史 Markdown 转成 EPUB 3 电子书(纯标准库,零依赖)

用法:
  python3 md2epub.py <编年史.md> <输出.epub> [--site 在线书目录] [--cover 封面.png] [--author 作者]

行为:
  - 标题取自文档第一个 # 标题,语言默认 zh,日期默认今天
  - 图片按 Markdown 相对路径解析,复制进电子书
  - Mermaid 代码块按顺序尝试渲染:本机 mmdc → kroki 在线服务 → 降级为代码块
  - 自动生成目录(nav)与封面页(有封面图时)
  - 加 --site 时额外输出在线书站点:目录页加分章页,浏览器端用
    mermaid.js 渲染图,整个目录扔到任意静态托管即上线
"""
import base64
import datetime
import html
import os
import re
import subprocess
import sys
import urllib.request
import zlib
import zipfile

def log(msg):
    print(f"[md2epub] {msg}")

def extract_meta(md_text, author):
    """从文档提取标题与整理日期。"""
    title = "编年史"
    m = re.search(r"^#\s+(.+)$", md_text, re.M)
    if m:
        title = m.group(1).strip()
    date = datetime.date.today().isoformat()
    m = re.search(r"整理日期\s+(\d{4}-\d{2}-\d{2})", md_text)
    if m:
        date = m.group(1)
    return title, date

def render_mermaid(code, index, workdir):
    """把 Mermaid 源码渲染成 PNG。返回图片文件名,失败返回 None。"""
    dest = os.path.join(workdir, "images", f"mermaid-{index}.png")
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    # 路径 1:本机 mmdc
    if shutil_which("mmdc"):
        src = os.path.join(workdir, f"mermaid-{index}.mmd")
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            subprocess.run(
                ["mmdc", "-i", src, "-o", dest, "-b", "white"],
                check=True, capture_output=True, timeout=60)
            return f"images/mermaid-{index}.png"
        except Exception:
            pass

    # 路径 2:kroki 在线服务
    try:
        payload = zlib.compress(code.encode("utf-8"))
        b64 = base64.urlsafe_b64encode(payload).decode("ascii")
        url = f"https://kroki.io/mermaid/png/{b64}"
        req = urllib.request.Request(url, headers={"User-Agent": "md2epub"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(dest, "wb") as f:
                f.write(resp.read())
        return f"images/mermaid-{index}.png"
    except Exception:
        pass

    return None

def shutil_which(name):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.exists(os.path.join(p, name)):
            return os.path.join(p, name)
    return None

def inline(text):
    """处理行内格式:**粗体**、`代码`、[链接](url)、![图](url)。图片替换必须先于链接,否则 ![图](url) 会被链接正则吞成 !<a>。"""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img alt="\1" src="\2"/>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    return text

def parse_blocks(lines, md_dir, image_dir, mermaid_mode="render"):
    """Markdown 子集解析:标题、段落、列表、表格、代码块、引用、图片、Mermaid。

    mermaid_mode 为 "render" 时尝试渲染成 PNG(EPUB 用),为 "keep" 时
    保留源码块并标记 class="mermaid",交给浏览器端 mermaid.js 渲染(在线书用)。
    """
    body = []
    mermaid_count = 0
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip("\n")

        if line.startswith("```"):
            lang = line[3:].strip()
            code = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                code.append(lines[i].rstrip("\n"))
                i += 1
            i += 1
            code_text = "\n".join(code)
            if lang == "mermaid":
                mermaid_count += 1
                if mermaid_mode == "keep":
                    body.append(f'<pre class="mermaid">{html.escape(code_text)}</pre>')
                else:
                    img = render_mermaid(code_text, mermaid_count, image_dir)
                    if img:
                        body.append(f'<figure><img src="{img}" alt="mermaid 图"/></figure>')
                    else:
                        body.append("<pre>Mermaid 图(阅读器不支持渲染,见源稿):</pre>")
                        body.append(f"<pre>{html.escape(code_text)}</pre>")
            else:
                body.append(f"<pre>{html.escape(code_text)}</pre>")
            continue

        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            body.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if re.match(r"^>\s?", line):
            quote = []
            while i < n and re.match(r"^>\s?", lines[i]):
                quote.append(re.sub(r"^>\s?", "", lines[i]).rstrip("\n"))
                i += 1
            body.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
            continue

        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+\.\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            items = []
            while i < n:
                cur = lines[i].rstrip("\n")
                m = re.match(r"^\s*(?:[-*]|\d+\.)\s+(.+)$", cur)
                if m:
                    items.append(inline(m.group(1)))
                    i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            body.append(f"<{tag}>" + "".join(f"<li>{it}</li>" for it in items) + f"</{tag}>")
            continue

        if line.startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|", lines[i + 1]):
            header = [c.strip() for c in line.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")])
                i += 1
            body.append("<table><thead><tr>" + "".join(f"<th>{inline(h)}</th>" for h in header) + "</tr></thead><tbody>")
            for row in rows:
                body.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            body.append("</tbody></table>")
            continue

        if line.strip() == "":
            i += 1
            continue

        # 普通段落,可能多行
        para = [line]
        i += 1
        while i < n:
            nxt = lines[i].rstrip("\n")
            if nxt.strip() == "" or re.match(r"^(#{1,4}\s|```|>\s?|[-*]\s+|\d+\.\s+)", nxt):
                break
            para.append(nxt)
            i += 1
        body.append(f"<p>{inline(' '.join(para))}</p>")

    return "\n".join(body)

def make_epub(md_path, out_path, cover_path, author):
    md_dir = os.path.dirname(os.path.abspath(md_path))
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    book_title, book_date = extract_meta(md_text, author)

    epub_dir = os.path.join(os.path.dirname(os.path.abspath(out_path)), ".epub-build")
    oebps = os.path.join(epub_dir, "OEBPS")
    os.makedirs(os.path.join(oebps, "images"), exist_ok=True)

    # 图片:按相对路径复制进 images/
    img_map = {}
    for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)\)", md_text):
        src = os.path.join(md_dir, m.group(1))
        if os.path.exists(src):
            name = os.path.basename(m.group(1))
            dst = os.path.join(oebps, "images", name)
            if not os.path.exists(dst):
                with open(src, "rb") as f:
                    with open(dst, "wb") as g:
                        g.write(f.read())
            img_map[m.group(1)] = f"images/{name}"

    # 解析正文
    body = parse_blocks(md_text.splitlines(), md_dir, oebps)
    for old, new in img_map.items():
        body = body.replace(f'src="{old}"', f'src="{new}"')

    # 封面页
    cover_html = ""
    cover_manifest = ""
    if cover_path and os.path.exists(cover_path):
        cover_name = "cover.png"
        with open(cover_path, "rb") as f:
            with open(os.path.join(oebps, "images", cover_name), "wb") as g:
                g.write(f.read())
        cover_html = '<div style="text-align:center;margin:10% 0;"><img src="images/cover.png" alt="封面" style="max-width:100%;"/></div>'
        cover_manifest = '<meta name="cover" content="cover-image"/>'
        cover_item = '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>'
    else:
        cover_item = ""

    # 正文 xhtml(拆章:按 h2 切分,便于目录)
    chapter_titles = [("chapter-1.xhtml", "开始")]
    body_chunks = re.split(r"(?=<h2>)", body)
    nav_items = []
    spine_items = []
    manifest_items = []
    chapter_id = 0
    css = """body { font-family: serif; line-height: 1.7; margin: 5%; }
h1 { text-align: center; margin-top: 20%; }
h2 { margin-top: 2em; border-bottom: 1px solid #999; }
h3 { margin-top: 1.5em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #999; padding: 4px 8px; font-size: 0.9em; }
pre { background: #f5f2ea; padding: 8px; white-space: pre-wrap; font-size: 0.85em; }
blockquote { color: #555; border-left: 3px solid #bbb; padding-left: 12px; margin: 1em 0; }
img { max-width: 100%; }
figure { margin: 1.5em 0; text-align: center; }
"""

    with open(os.path.join(oebps, "styles.css"), "w", encoding="utf-8") as f:
        f.write(css)
    manifest_items.append('<item id="css" href="styles.css" media-type="text/css"/>')

    def add_chapter(fname, title, content_html):
        nonlocal chapter_id
        chapter_id += 1
        with open(os.path.join(oebps, fname), "w", encoding="utf-8") as f:
            f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh">
<head><title>{html.escape(title)}</title>
<link rel="stylesheet" type="text/css" href="styles.css"/></head>
<body>
{content_html}
</body>
</html>
""")
        nav_items.append(f'<li><a href="{fname}">{html.escape(title)}</a></li>')
        spine_items.append(f'<itemref idref="ch{chapter_id}"/>')
        manifest_items.append(f'<item id="ch{chapter_id}" href="{fname}" media-type="application/xhtml+xml"/>')

    # 封面章
    if cover_html:
        add_chapter("cover.xhtml", "封面", cover_html + "<p><a href=\"chapter-1.xhtml\">开始阅读</a></p>")

    if cover_html:
        manifest_items.append(cover_item)

    first = True
    for chunk in body_chunks:
        if chunk.strip() == "":
            continue
        m = re.search(r"<h2>(.+?)</h2>", chunk)
        title = m.group(1) if m else ("正文" if first else "续")
        fname = f"chapter-{chapter_id + 1}.xhtml"
        add_chapter(fname, title, chunk)
        first = False

    # nav
    with open(os.path.join(oebps, "nav.xhtml"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>目录</title></head>
<body>
<nav epub:type="toc"><h1>目录</h1><ol>{''.join(nav_items)}</ol></nav>
</body>
</html>
""")
    manifest_items.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')

    # opf
    with open(os.path.join(oebps, "content.opf"), "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">urn:uuid:{uuid4()}</dc:identifier>
<dc:title>{html.escape(book_title)}</dc:title>
<dc:creator>{html.escape(author or "未知")}</dc:creator>
<dc:language>zh</dc:language>
<dc:date>{book_date}</dc:date>
{cover_manifest}
</metadata>
<manifest>
{''.join(manifest_items)}
</manifest>
<spine>{''.join(spine_items)}</spine>
</package>
""")

    # container.xml 与 mimetype
    meta_inf = os.path.join(epub_dir, "META-INF")
    os.makedirs(meta_inf, exist_ok=True)
    with open(os.path.join(meta_inf, "container.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')

    with open(os.path.join(epub_dir, "mimetype"), "w") as f:
        f.write("application/epub+zip")

    # 打包: mimetype 必须第一个且不压缩
    with zipfile.ZipFile(out_path, "w") as zf:
        zf.write(os.path.join(epub_dir, "mimetype"), "mimetype", compress_type=zipfile.ZIP_STORED)
        for root, _, files in os.walk(epub_dir):
            for name in files:
                if name == "mimetype":
                    continue
                full = os.path.join(root, name)
                arc = os.path.relpath(full, epub_dir)
                zf.write(full, arc, compress_type=zipfile.ZIP_DEFLATED)

    log(f"完成: {out_path}  ({book_title} / {author} / {book_date})")
    return out_path

SITE_CSS = """body { font-family: "Songti SC", "Noto Serif CJK SC", serif; line-height: 1.8; color: #2b2b2b; background: #faf8f4; margin: 0; }
.book-home { max-width: 720px; margin: 0 auto; padding: 48px 24px; text-align: center; }
.book-cover { max-width: 320px; box-shadow: 0 4px 16px rgba(0,0,0,.15); margin-bottom: 24px; }
.book-toc { list-style: none; padding: 0; text-align: left; }
.book-toc li { margin: 10px 0; }
.book-toc a { text-decoration: none; color: #2b2b2b; }
.book-toc a:hover { color: #8a5a2b; }
.book-nav { max-width: 720px; margin: 0 auto; padding: 12px 24px; font-size: .9em; color: #666; }
.book-nav a { color: #666; text-decoration: none; margin: 0 4px; }
.chapter { max-width: 720px; margin: 0 auto; padding: 24px; }
.chapter h1 { text-align: center; }
.chapter h2 { margin-top: 2em; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #999; padding: 6px 10px; font-size: .92em; }
pre { background: #f1ede4; padding: 10px; overflow-x: auto; font-size: .88em; }
blockquote { color: #555; border-left: 3px solid #bbb; padding-left: 12px; margin: 1em 0; }
img { max-width: 100%; }
figure { margin: 1.5em 0; text-align: center; }
"""

def make_site(md_path, site_dir, cover_path, author):
    """生成可部署的在线书站点:目录页 + 分章页,浏览器端渲染 Mermaid。"""
    md_dir = os.path.dirname(os.path.abspath(md_path))
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    book_title, book_date = extract_meta(md_text, author)

    chapters_dir = os.path.join(site_dir, "chapters")
    images_dir = os.path.join(site_dir, "images")
    os.makedirs(chapters_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    img_map = {}
    for m in re.finditer(r"!\[[^\]]*\]\(([^)\s]+)\)", md_text):
        src = os.path.join(md_dir, m.group(1))
        if os.path.exists(src):
            name = os.path.basename(m.group(1))
            dst = os.path.join(images_dir, name)
            if not os.path.exists(dst):
                with open(src, "rb") as f, open(dst, "wb") as g:
                    g.write(f.read())
            img_map[m.group(1)] = f"../images/{name}"

    body = parse_blocks(md_text.splitlines(), md_dir, site_dir, mermaid_mode="keep")
    for old, new in img_map.items():
        body = body.replace(f'src="{old}"', f'src="{new}"')

    chunks = [c for c in re.split(r"(?=<h2>)", body) if c.strip()]
    chapters = []
    for chunk in chunks:
        m = re.search(r"<h2>(.+?)</h2>", chunk)
        chapters.append((m.group(1) if m else "开篇", chunk))

    cover_html = ""
    if cover_path and os.path.exists(cover_path):
        name = "cover.png"
        with open(cover_path, "rb") as f, open(os.path.join(images_dir, name), "wb") as g:
            g.write(f.read())
        cover_html = '<img class="book-cover" src="images/cover.png" alt="封面"/>'

    total = len(chapters)
    nav_links = []
    for idx, (title, chunk) in enumerate(chapters):
        fname = f"ch-{idx + 1:02d}.html"
        nav = '<a href="../index.html">目录</a>'
        if idx > 0:
            nav += f' · <a href="ch-{idx:02d}.html">上一章</a>'
        if idx < total - 1:
            nav += f' · <a href="ch-{idx + 2:02d}.html">下一章</a>'
        with open(os.path.join(chapters_dir, fname), "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)} - {html.escape(book_title)}</title>
<link rel="stylesheet" href="../styles.css"/>
</head>
<body>
<nav class="book-nav">{nav}</nav>
<main class="chapter">
{chunk}
</main>
<footer class="book-nav">{nav}</footer>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, theme:'neutral'}});</script>
</body>
</html>
""")
        nav_links.append((title, fname))

    toc = "\n".join(
        f'<li><a href="chapters/{fname}">{html.escape(title)}</a></li>'
        for title, fname in nav_links)
    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(book_title)}</title>
<link rel="stylesheet" href="styles.css"/>
</head>
<body>
<main class="book-home">
{cover_html}
<h1>{html.escape(book_title)}</h1>
<p class="book-meta">{html.escape(author or "未知")} · {book_date}</p>
<ol class="book-toc">{toc}</ol>
</main>
</body>
</html>
""")

    with open(os.path.join(site_dir, "styles.css"), "w", encoding="utf-8") as f:
        f.write(SITE_CSS)

    log(f"完成: {site_dir}  ({total} 章,在线书)")
    return site_dir

def uuid4():
    import uuid
    return uuid.uuid4()

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    md_path = sys.argv[1]
    out_path = sys.argv[2]
    cover = None
    author = None
    site = None
    if "--cover" in sys.argv:
        cover = sys.argv[sys.argv.index("--cover") + 1]
    if "--author" in sys.argv:
        author = sys.argv[sys.argv.index("--author") + 1]
    if "--site" in sys.argv:
        site = sys.argv[sys.argv.index("--site") + 1]
    if not os.path.exists(md_path):
        print(f"错误: 找不到 {md_path}", file=sys.stderr)
        sys.exit(1)
    make_epub(md_path, out_path, cover, author)
    if site:
        make_site(md_path, site, cover, author)

if __name__ == "__main__":
    main()
