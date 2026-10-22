#!/usr/bin/env python3
"""Collect an incremental evidence batch and append reviewed Markdown without rewriting it."""

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("时间必须为带时区的 ISO 8601，例如 2026-08-14T23:59:59+08:00") from exc
    if result.tzinfo is None:
        raise ValueError("时间必须包含时区")
    return result.astimezone(timezone.utc)


def iso(value):
    return timestamp(value).isoformat().replace("+00:00", "Z")


def git(repo, *args, check=True):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and result.returncode:
        raise ValueError(result.stderr.strip() or "Git 命令失败")
    return result


def commit(repo, ref):
    # --end-of-options keeps ref names from becoming command options.
    return git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").stdout.strip()


def repository(repo, head):
    remote = git(repo, "remote", "get-url", "origin", check=False)
    url = remote.stdout.strip().rstrip("/") if remote.returncode == 0 else ""
    url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
    url = re.sub(r"^ssh://git@", "https://", url)
    if url.endswith(".git"):
        url = url[:-4]
    roots = sorted(git(repo, "rev-list", "--max-parents=0", head, "--").stdout.splitlines())
    return {"origin": url, "roots": roots}


def validate_repository(repo, state, head):
    identity = repository(repo, head)
    expected = state["repository"]
    if identity["origin"] != expected["origin"] or not set(expected["roots"]).issubset(identity["roots"]):
        raise ValueError("仓库身份与截点不符，请检查 origin 和仓库路径")
    base = commit(repo, state["commit"])
    if git(repo, "merge-base", "--is-ancestor", base, head, check=False).returncode:
        raise ValueError("截点不是目标提交的祖先，不能自动续写重写后的历史")


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path):
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def read_state(path):
    state = read_json(path)
    if state.get("version") != 1:
        raise ValueError("不支持的截点版本")
    return state


def document_path(checkpoint, state):
    return (Path(checkpoint).resolve().parent / state["document"]["path"]).resolve()


def checked_document(checkpoint, state):
    data = document_path(checkpoint, state).read_bytes()
    if digest(data) != state["document"]["sha256"] or len(data) != state["document"]["bytes"]:
        raise ValueError("旧稿与截点校验和不符；请恢复旧稿，修正内容另写勘误")
    return data


def init(args):
    checkpoint = Path(args.checkpoint).resolve()
    document = Path(args.document).resolve()
    if checkpoint == document:
        raise ValueError("截点文件不能覆盖正文")
    if checkpoint.exists():
        raise ValueError("截点已存在，拒绝覆盖")
    data = document.read_bytes()
    if not data.decode("utf-8").strip():
        raise ValueError("初稿不能为空")
    head = commit(args.repo, args.commit)
    through = iso(args.through)
    state = {
        "version": 1,
        "repository": repository(args.repo, head),
        "commit": head,
        "through": through,
        "source_through": {"releases": through, "community": through},
        "source_seen": {"releases": [], "community": []},
        "document": {"path": os.path.relpath(document, checkpoint.parent), "sha256": digest(data), "bytes": len(data)},
        "last_batch": None,
    }
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects an existing checkpoint from accidental reinitialization.
    with checkpoint.open("xb") as stream:
        stream.write(encoded(state))
    print("已记录初稿截点 " + head)


def filtered_sources(path, kind, state, through):
    lower = state["source_through"][kind]
    seen = set(state["source_seen"][kind])
    if path is None:
        return [], [{"status": "unavailable", "reason": "未提供 " + kind + " 数据，时间水位保持不变"}], lower, sorted(seen)
    records = read_json(path)
    if not isinstance(records, list):
        raise ValueError(kind + " 输入必须是 JSON 数组")
    selected, gaps, batch_ids = [], [], set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError(kind + " 每条记录必须是 JSON 对象")
        if record.get("status") == "unavailable":
            gaps.append(record)
            continue
        if record.get("status", "ok") != "ok":
            raise ValueError(kind + " status 只能为 ok 或 unavailable")
        date = record.get("publishedAt") or record.get("published_at")
        date = iso(date)
        key = record.get("url") if kind == "community" else (record.get("id") or record.get("tagName") or record.get("tag_name") or record.get("url"))
        if not key:
            raise ValueError(kind + " 记录缺少 url 或 release 标识")
        event_id = digest(encoded([str(key), date]))
        if timestamp(lower) < timestamp(date) <= timestamp(through) and event_id not in seen and event_id not in batch_ids:
            selected.append(record)
            batch_ids.add(event_id)
    # A partial fetch cannot acknowledge an entire time window. Remember emitted
    # records until the missing source is recovered, so retries do not duplicate them.
    next_through = lower if gaps else through
    next_seen = sorted(seen | batch_ids) if gaps else []
    return selected, gaps, next_through, next_seen


def collect(args):
    state = read_state(args.checkpoint)
    checked_document(args.checkpoint, state)
    head = commit(args.repo, args.to)
    validate_repository(args.repo, state, head)
    through = iso(args.through)
    if timestamp(through) < timestamp(state["through"]):
        raise ValueError("新截点日期不能早于现有截点")
    out = Path(args.out)
    if out.exists():
        raise ValueError("批次输出目录已存在，请使用新的目录")
    revision = state["commit"] + ".." + head
    raw = git(args.repo, "log", "--reverse", "--topo-order", "--format=%H%x09%an%x09%ae%x09%cI%x09%s", revision, "--").stdout
    rows = [line.split("\t", 4) for line in raw.splitlines()]
    per_year, per_month, per_author = collections.defaultdict(list), collections.defaultdict(list), collections.Counter()
    for row in rows:
        per_year[row[3][:4]].append(row[2])
        per_month[row[3][:7]].append(row[2])
        per_author[(row[1], row[2])] += 1
    outputs = {
        "commits.tsv": raw.encode("utf-8"),
        "commits_full.log": git(args.repo, "log", "--reverse", "--topo-order", "--format=commit %H%nAuthor: %an <%ae>%nDate: %cI%n%n%B%n---", revision, "--").stdout.encode("utf-8"),
        "per_year.tsv": "".join(f"{key}\t{len(values)}\t{len(set(values))}\n" for key, values in sorted(per_year.items())).encode("utf-8"),
        "per_month.tsv": "".join(f"{key}\t{len(values)}\t{len(set(values))}\n" for key, values in sorted(per_month.items())).encode("utf-8"),
        "per_author.tsv": "".join(f"{count}\t{name}\t{email}\n" for (name, email), count in sorted(per_author.items(), key=lambda pair: (-pair[1], pair[0]))).encode("utf-8"),
    }
    next_sources, next_seen, counts = {}, {}, {"commits": len(rows)}
    for kind in ("releases", "community"):
        selected, gaps, next_sources[kind], next_seen[kind] = filtered_sources(getattr(args, kind), kind, state, through)
        outputs[kind + ".json"] = encoded(selected)
        outputs[kind + "-gaps.json"] = encoded(gaps)
        counts[kind] = len(selected)
    batch = {
        "version": 1, "base": state, "to_commit": head, "through": through,
        "source_through": next_sources, "source_seen": next_seen, "counts": counts,
        "files": {name: digest(data) for name, data in outputs.items()},
    }
    batch["id"] = digest(encoded(batch))
    out.mkdir(parents=True)
    for name, data in outputs.items():
        atomic_write(out / name, data)
    atomic_write(out / "batch.json", encoded(batch))
    print(json.dumps({"batch": str(out / "batch.json"), "counts": counts}, ensure_ascii=False))


def append(args):
    state = read_state(args.checkpoint)
    batch_path = Path(args.batch).resolve()
    batch = read_json(batch_path)
    batch_id = batch.get("id")
    if digest(encoded({key: value for key, value in batch.items() if key != "id"})) != batch_id:
        raise ValueError("批次清单校验失败，请重新采集")
    if state.get("last_batch") == batch_id:
        checked_document(args.checkpoint, state)
        print("本批次已追加，未重复写入")
        return
    if state != batch["base"]:
        raise ValueError("批次已过期，必须从当前截点重新采集")
    validate_repository(args.repo, state, commit(args.repo, batch["to_commit"]))
    for name, expected in batch["files"].items():
        if Path(name).name != name or digest((batch_path.parent / name).read_bytes()) != expected:
            raise ValueError("采集材料校验失败: " + name)
    if not any(batch["counts"].values()) and not args.erratum:
        raise ValueError("没有新提交或来源，不追加空章节；有核实后的修正可使用 --erratum")
    chapter = Path(args.chapter).read_text(encoding="utf-8").strip()
    if not chapter.startswith("## "):
        raise ValueError("新增稿必须从二级章节标题（## ）开始")
    if args.erratum and not chapter.startswith("## 勘误"):
        raise ValueError("--erratum 需要以 ## 勘误 开头")
    path = document_path(args.checkpoint, state)
    current = path.read_bytes()
    original_size = state["document"]["bytes"]
    original = current[:original_size]
    if digest(original) != state["document"]["sha256"]:
        raise ValueError("旧稿正文已变化，拒绝续写；请恢复旧稿并追加勘误")
    suffix = (b"\n" if original.endswith(b"\n") else b"\n\n") + chapter.encode("utf-8") + b"\n"
    updated = original + suffix
    # If the first replace succeeded but checkpoint update failed, the same
    # batch/chapter can finish the checkpoint update without writing twice.
    if current != original and current != updated:
        raise ValueError("正文含有其他追加内容，与当前批次不符")
    new_state = dict(state, commit=batch["to_commit"], through=batch["through"],
                     source_through=batch["source_through"], source_seen=batch["source_seen"], last_batch=batch_id)
    new_state["document"] = dict(state["document"], sha256=digest(updated), bytes=len(updated))
    if current == original:
        atomic_write(path, updated)
    atomic_write(args.checkpoint, encoded(new_state))
    print("已追加章节并推进截点 " + batch["to_commit"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("init", init), ("collect", collect), ("append", append)):
        command_parser = commands.add_parser(name)
        command_parser.add_argument("--repo", required=True)
        command_parser.add_argument("--checkpoint", required=True)
        command_parser.set_defaults(handler=handler)
        if name == "init":
            command_parser.add_argument("--document", required=True)
            command_parser.add_argument("--commit", default="HEAD")
            command_parser.add_argument("--through", required=True)
        elif name == "collect":
            command_parser.add_argument("--out", required=True)
            command_parser.add_argument("--to", default="HEAD")
            command_parser.add_argument("--through", required=True)
            command_parser.add_argument("--releases")
            command_parser.add_argument("--community")
        else:
            command_parser.add_argument("--batch", required=True)
            command_parser.add_argument("--chapter", required=True)
            command_parser.add_argument("--erratum", action="store_true")
    args = parser.parse_args()
    try:
        args.handler(args)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, "错误: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
