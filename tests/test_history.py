"""Exercise the exporter against real, isolated Git histories."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/git-repo-chronicle/scripts/dump_git_history.sh"


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "a repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture Author")
        self.git("config", "user.email", "author@example.test")

    def git(self, *args, env=None):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], text=True,
            env={**os.environ, **(env or {})}, stderr=subprocess.PIPE,
        ).strip()

    def commit(self, title, author_date="2024-12-31T23:30:00+00:00",
               commit_date="2025-01-01T00:30:00+08:00"):
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", title,
                 env={"GIT_AUTHOR_DATE": author_date, "GIT_COMMITTER_DATE": commit_date})
        return self.git("rev-parse", "HEAD")

    def export(self, *flags, repo=None, output="output data"):
        subprocess.run(["bash", str(SCRIPT), str(repo or self.repo), output, *flags],
                       cwd=self.root, check=True, capture_output=True, text=True)
        return self.root / output

    def test_relative_output_and_committer_month(self):
        commit = self.commit("original")
        out = self.export()
        row = (out / "commits.tsv").read_text().strip().split("\t")
        self.assertEqual(row[0], commit)
        self.assertEqual(row[3], "2025-01-01T00:30:00+08:00")
        self.assertEqual((out / "per_month.tsv").read_text(), "2025-01\t1\t1\n")
        self.assertEqual((out / "per_year.tsv").read_text(), "2025\t1\t1\n")
        self.assertEqual((out / "per_author.tsv").read_text(), "1\tFixture Author\tauthor@example.test\n")
        self.assertFalse((self.repo / "output data").exists())

    def test_first_parent_count_matches_export_and_aggregates(self):
        self.commit("root")
        main = self.git("branch", "--show-current")
        self.git("checkout", "-q", "-b", "feature")
        feature = self.commit("feature")
        self.git("checkout", "-q", main)
        self.commit("main")
        self.git("-c", "commit.gpgsign=false", "merge", "--no-ff", "feature", "-m", "merge")
        out = self.export("--first-parent")
        rows = (out / "commits.tsv").read_text().splitlines()
        self.assertEqual(len(rows), 3)
        self.assertNotIn(feature, (out / "commits.tsv").read_text())
        self.assertIn("总提交数: 3\n", (out / "meta.txt").read_text())
        self.assertEqual(sum(int(row.split("\t")[1]) for row in (out / "per_month.tsv").read_text().splitlines()), 3)
        complete = self.export(output="complete")
        self.assertEqual(len((complete / "commits.tsv").read_text().splitlines()), 4)

    def test_worktree_is_supported(self):
        self.commit("root")
        worktree = self.root / "linked worktree"
        self.git("worktree", "add", "--detach", str(worktree), "HEAD")
        out = self.export(repo=worktree)
        self.assertEqual(len((out / "commits.tsv").read_text().splitlines()), 1)

    def test_empty_repository(self):
        out = self.export()
        for name in ("commits.tsv", "commits_full.log", "per_month.tsv", "per_year.tsv", "per_author.tsv", "tags.tsv"):
            self.assertEqual((out / name).read_bytes(), b"")
        self.assertIn("总提交数: 0\n", (out / "meta.txt").read_text())

    def test_invalid_flag_rejected_before_export(self):
        result = subprocess.run(["bash", str(SCRIPT), str(self.repo), "output", "--typo"],
                                cwd=self.root, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "output").exists())


if __name__ == "__main__":
    unittest.main()
