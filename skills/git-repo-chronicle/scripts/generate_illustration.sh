#!/usr/bin/env bash
#
# generate_illustration.sh — 调用生图 API 生成手绘风插图
#
# 用法:  generate_illustration.sh <提示词> <输出路径> [尺寸]
#   例:  scripts/generate_illustration.sh "ink sketch of a server room, vintage chronicle style" docs/notes/images/server-room.png
#
# 环境变量(由用户提供,缺任一配置则报错退出):
#   ILLUSTRATION_BASE_URL  生图服务地址,如 https://api.example.com/v1
#   ILLUSTRATION_API_KEY   API 密钥
#   ILLUSTRATION_MODEL     模型名
#
# 协议: OpenAI 兼容的 /images/generations。
# 先按 url 模式请求,失败后自动重试 b64_json 模式,两种响应都能存图。
# 依赖: curl、python3(标准库即可,不需要 jq)。
set -euo pipefail

PROMPT="${1:?用法: generate_illustration.sh <提示词> <输出路径> [尺寸]}"
OUT="${2:?用法: generate_illustration.sh <提示词> <输出路径> [尺寸]}"
SIZE="${3:-1024x1024}"

: "${ILLUSTRATION_BASE_URL:?缺少 ILLUSTRATION_BASE_URL,请先设置生图配置}"
: "${ILLUSTRATION_API_KEY:?缺少 ILLUSTRATION_API_KEY}"
: "${ILLUSTRATION_MODEL:?缺少 ILLUSTRATION_MODEL}"

mkdir -p "$(dirname "$OUT")"
URL="${ILLUSTRATION_BASE_URL%/}/images/generations"
AUTH="Authorization: Bearer $ILLUSTRATION_API_KEY"
RESP="$(mktemp)"
trap 'rm -f "$RESP"' EXIT

# 从响应 JSON 里取出图片并保存。$1 是响应模式(url / b64),$2 是输出路径。
SAVE_PY='
import json, sys, base64, urllib.request
mode, out = sys.argv[1], sys.argv[2]
try:
    data = json.load(sys.stdin)
    item = data["data"][0]
except Exception:
    sys.exit(2)
if mode == "url" and "url" in item:
    urllib.request.urlretrieve(item["url"], out)
elif mode == "b64" and "b64_json" in item:
    open(out, "wb").write(base64.b64decode(item["b64_json"]))
else:
    sys.exit(2)
'

# 模式一: url 模式(不带 response_format,兼容面最广)
BODY_URL=$(python3 -c 'import json,sys; print(json.dumps({"model": sys.argv[1], "prompt": sys.argv[2], "n": 1, "size": sys.argv[3]}))' \
  "$ILLUSTRATION_MODEL" "$PROMPT" "$SIZE")

if curl -sf -X POST "$URL" -H "$AUTH" -H "Content-Type: application/json" -d "$BODY_URL" > "$RESP" \
    && python3 -c "$SAVE_PY" url "$OUT" < "$RESP"; then
  echo "插图已生成: $OUT"
  exit 0
fi

# 模式二: b64_json 模式(兼容本地部署与中转)
BODY_B64=$(python3 -c 'import json,sys; print(json.dumps({"model": sys.argv[1], "prompt": sys.argv[2], "n": 1, "size": sys.argv[3], "response_format": "b64_json"}))' \
  "$ILLUSTRATION_MODEL" "$PROMPT" "$SIZE")

if curl -sf -X POST "$URL" -H "$AUTH" -H "Content-Type: application/json" -d "$BODY_B64" > "$RESP" \
    && python3 -c "$SAVE_PY" b64 "$OUT" < "$RESP"; then
  echo "插图已生成: $OUT"
  exit 0
fi

echo "错误: 生图请求失败。请检查 ILLUSTRATION_BASE_URL / API_KEY / MODEL 三项配置和网络。" >&2
exit 1
