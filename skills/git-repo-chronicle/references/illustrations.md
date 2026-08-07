# 编年史插图规范

插图是可选能力。用户提供生图模型的三项配置(base_url、api_key、model),就按本文生成手绘风插图,给编年史配"老相册"气质。缺配置或生成失败,直接跳过,不影响交稿。

## 风格定义

所有插图共用一个风格前缀,保证全篇一致:

```text
Hand-drawn illustration in the style of a vintage chronicle book. Ink sketch with light watercolor wash, aged paper texture, muted sepia and indigo palette, storytelling scene, atmospheric, no text, no watermark, no logo.
```

主题描述接在风格前缀后面,写具体场景。主题按项目实际写,英文优先,中文亦可。

## 配置

用户提供三项,设成环境变量:

```bash
export ILLUSTRATION_BASE_URL="https://api.example.com/v1"
export ILLUSTRATION_API_KEY="sk-xxxx"
export ILLUSTRATION_MODEL="gpt-image-1"
```

协议是 OpenAI 兼容的 images/generations,大多数服务都支持,包括各类中转与本地部署。

## 调用

```bash
scripts/generate_illustration.sh "风格前缀 + 主题" docs/notes/images/2020-migration.png
```

默认尺寸 1024x1024,第三个参数可改。脚本先按 url 模式请求,失败自动重试 b64_json 模式,两种响应都能存图。

## 主题清单

按章节给建议,实际按项目内容调整:

| 位置 | 建议主题 |
|---|---|
| 题头封面 | 项目核心意象,如手绘的服务器机房、笔记簿、引擎齿轮 |
| §0 | 诞生场景,如窗台前的笔记本和咖啡 |
| 架构转型章 | 新旧交替,如旧书和新书并排、两代机器的轮廓 |
| 里程碑章 | 该版本的代表场景,如命令行窗口里的绿色字样 |
| 停更章 | 空房间、熄灯的窗口 |
| 复活章 | 重新点亮的灯、晨光中的工作台 |
| §11 论坛回声 | 一群人围桌讨论、公告板上的纸条 |

## 图片嵌入

图片统一放 `docs/notes/images/`,Markdown 相对路径引用:

```markdown
![2020 年架构迁移后的服务端](images/2020-migration.png)
```

## 失败降级

1. 脚本先试 url 模式,再试 b64_json 模式。
2. 都失败时,检查三项配置和网络,可重试一次。
3. 仍失败,跳过插图,在交稿说明里告诉用户"配图因生图服务不可用已跳过"。
4. 不生成真人肖像。人物相关的主题一律用工作台、工具、场景等意象代替。

## 校验

1. 每张图与所在章节内容对应,不画与正文无关的东西。
2. 全篇风格一致,都用同一风格前缀。
3. 图片文件存在,引用路径能打开。
4. 插图的提示词与生成参数记在文末方法论注记里(可选)。
