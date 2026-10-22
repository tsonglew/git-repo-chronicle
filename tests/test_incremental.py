import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone


SCRIPT = Path(__file__).resolve().parents[1] / "skills/git-repo-chronicle/scripts/chronicle_checkpoint.py"


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture Author")
        self.git("config", "user.email", "fixture@example.invalid")
        self.first = self.make_commit("first", "2025-01-01T12:00:00+00:00")
        self.document = self.root / "chronicle.md"
        self.original = "# 编年史\n\n## §1 2025 初创 · 首次发布\n\n第一章正文永不改写。\n".encode("utf-8")
        self.document.write_bytes(self.original)
        self.checkpoint = self.root / "chronicle-checkpoint.json"
        self.run_script("init", "--document", str(self.document), "--through", "2025-01-01T23:59:59Z")

    def git(self, *args, env=None):
        result = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def make_commit(self, name, date, author_date=None):
        (self.repo / "story.txt").write_text(name, encoding="utf-8")
        self.git("add", "story.txt")
        env = dict(os.environ, GIT_AUTHOR_DATE=author_date or date, GIT_COMMITTER_DATE=date)
        self.git("commit", "-qm", name, env=env)
        return self.git("rev-parse", "HEAD")

    def run_script(self, command, *args, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), command, "--repo", str(self.repo),
                                 "--checkpoint", str(self.checkpoint), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def collect(self, name, through="2025-02-01T23:59:59Z", *args):
        out = self.root / name
        self.run_script("collect", "--out", str(out), "--through", through, *args)
        return out

    def chapter(self, name="new.md", text="## §2 2025 成长 · 新功能\n\n第二章的新内容。\n"):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def append(self, out, chapter=None, *args, success=True):
        return self.run_script("append", "--batch", str(out / "batch.json"), "--chapter", str(chapter or self.chapter()), *args, success=success)

    def json_file(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def state(self):
        return json.loads(self.checkpoint.read_text(encoding="utf-8"))

    def test_two_updates_preserve_first_chapter_and_retry_is_idempotent(self):
        second = self.make_commit("second", "2025-02-01T12:00:00Z", "2024-12-01T00:00:00Z")
        batch = self.collect("batch-1")
        rows = (batch / "commits.tsv").read_text().splitlines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].split("\t")[0], second)
        exported_date = datetime.fromisoformat(rows[0].split("\t")[3].replace("Z", "+00:00"))
        self.assertEqual(exported_date, datetime(2025, 2, 1, 12, tzinfo=timezone.utc))
        self.append(batch)
        after_first = self.document.read_bytes()
        self.assertTrue(after_first.startswith(self.original))
        self.append(batch)
        self.assertEqual(self.document.read_bytes(), after_first)
        third = self.make_commit("third", "2025-03-01T12:00:00Z")
        second_batch = self.collect("batch-2", "2025-03-01T23:59:59Z")
        self.assertEqual((second_batch / "commits.tsv").read_text().split("\t")[0], third)
        self.append(second_batch, self.chapter("third.md", "## §3 近况\n\n第三章。"))
        self.assertTrue(self.document.read_bytes().startswith(after_first))
        self.assertEqual(self.state()["document"]["sha256"], hashlib.sha256(self.document.read_bytes()).hexdigest())

    def test_source_windows_exclude_lower_boundary_and_future(self):
        self.make_commit("second", "2025-02-01T12:00:00Z")
        dates = ["2025-01-01T23:59:59Z", "2025-02-01T23:59:59Z", "2025-02-02T00:00:00Z"]
        releases = self.json_file("releases.json", [{"tagName": f"v{i}", "publishedAt": date} for i, date in enumerate(dates)])
        community = self.json_file("community.json", [{"url": f"https://example.invalid/{i}", "published_at": date, "status": "ok"} for i, date in enumerate(dates)])
        batch = self.collect("sources", "2025-02-01T23:59:59Z", "--releases", str(releases), "--community", str(community))
        self.assertEqual([r["tagName"] for r in json.loads((batch / "releases.json").read_text())], ["v1"])
        self.assertEqual([r["url"] for r in json.loads((batch / "community.json").read_text())], ["https://example.invalid/1"])
        self.append(batch)
        self.assertEqual(self.state()["source_through"], {"community": dates[1], "releases": dates[1]})

    def test_partial_community_fetch_keeps_watermark_and_deduplicates_recovery(self):
        good = {"url": "https://example.invalid/good", "published_at": "2025-01-20T12:00:00Z", "status": "ok"}
        gap = {"url": "https://example.invalid/gap", "published_at": None, "status": "unavailable", "reason": "login_required"}
        source = self.json_file("partial.json", [good, good, gap])
        batch = self.collect("partial", "2025-02-01T23:59:59Z", "--community", str(source))
        self.assertEqual(len(json.loads((batch / "community.json").read_text())), 1)
        self.assertEqual(json.loads((batch / "community-gaps.json").read_text()), [gap])
        self.append(batch)
        self.assertEqual(self.state()["source_through"]["community"], "2025-01-01T23:59:59Z")
        recovered = dict(gap, status="ok", published_at="2025-01-21T12:00:00Z")
        source = self.json_file("recovered.json", [good, recovered])
        next_batch = self.collect("recovered", "2025-03-01T23:59:59Z", "--community", str(source))
        self.assertEqual(json.loads((next_batch / "community.json").read_text()), [recovered])
        self.append(next_batch)
        self.assertEqual(self.state()["source_through"]["community"], "2025-03-01T23:59:59Z")
        self.assertEqual(self.state()["source_seen"]["community"], [])

    def test_tampering_never_advances_checkpoint(self):
        self.make_commit("second", "2025-02-01T12:00:00Z")
        batch = self.collect("tamper")
        original_state = self.checkpoint.read_bytes()
        self.document.write_bytes(self.original.replace("第一章".encode(), "改写了".encode()))
        self.append(batch, success=False)
        self.assertEqual(self.checkpoint.read_bytes(), original_state)
        self.run_script("collect", "--out", str(self.root / "more"), "--through", "2025-03-01T00:00:00Z", success=False)
        self.document.write_bytes(self.original)
        (batch / "commits.tsv").write_text("tampered")
        self.append(batch, success=False)
        self.assertEqual(self.checkpoint.read_bytes(), original_state)
        self.assertEqual(self.document.read_bytes(), self.original)

    def test_retry_finishes_checkpoint_after_interrupted_update(self):
        self.make_commit("second", "2025-02-01T12:00:00Z")
        batch = self.collect("interrupted")
        old_checkpoint = self.checkpoint.read_bytes()
        self.append(batch)
        updated_document = self.document.read_bytes()
        self.checkpoint.write_bytes(old_checkpoint)  # Simulate failure of the second atomic replace.
        self.append(batch)
        self.assertEqual(self.document.read_bytes(), updated_document)
        self.assertEqual(self.state()["commit"], self.git("rev-parse", "HEAD"))

    def test_stale_batch_and_diverged_history_are_rejected(self):
        self.make_commit("second", "2025-02-01T12:00:00Z")
        first_batch = self.collect("first-batch")
        stale_batch = self.collect("stale-batch", "2025-02-02T00:00:00Z")
        self.append(first_batch)
        self.append(stale_batch, success=False)
        self.git("checkout", "--detach", self.first)
        self.make_commit("diverged", "2025-03-01T12:00:00Z")
        result = self.run_script("collect", "--out", str(self.root / "diverged"), "--through", "2025-03-02T00:00:00Z", success=False)
        self.assertIn("祖先", result.stderr)
        self.assertFalse((self.root / "diverged").exists())

    def test_empty_batch_only_allows_explicit_erratum(self):
        batch = self.collect("empty")
        self.append(batch, success=False)
        self.append(batch, self.chapter("erratum.md", "## 勘误 2025-02\n\n上一章笔误说明，原稿保留。"), "--erratum")
        self.assertTrue(self.document.read_bytes().startswith(self.original))

    def test_invalid_source_date_does_not_create_batch_or_change_state(self):
        original_state = self.checkpoint.read_bytes()
        source = self.json_file("bad.json", [{"url": "https://example.invalid/item", "status": "ok", "published_at": None}])
        self.run_script("collect", "--out", str(self.root / "bad"), "--through", "2025-02-01T00:00:00Z", "--community", str(source), success=False)
        self.assertFalse((self.root / "bad").exists())
        self.assertEqual(self.checkpoint.read_bytes(), original_state)


if __name__ == "__main__":
    unittest.main()
