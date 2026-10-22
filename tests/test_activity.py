import importlib.util
import datetime as dt
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


SCRIPT = Path(__file__).resolve().parents[1] / "skills/git-repo-chronicle/scripts/render_activity.py"
SPEC = importlib.util.spec_from_file_location("render_activity", SCRIPT)
activity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(activity)


class ActivityTests(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "per_month.tsv"
            source.write_text(text, encoding="utf-8")
            return activity.read_months(source)

    def test_partial_year_distinguishes_zero_and_uncovered_and_escapes_text(self):
        rows = self.read("2026-02\t3\t2\n2026-03\t6\t1\n")
        svg = activity.render(rows, 2026, dt.date(2026, 3, 12), "A & <B>", "abc", "测试")
        root = ET.fromstring(svg)
        bars = {node.attrib["data-month"]: node.attrib for node in root.iter() if "data-month" in node.attrib}
        self.assertEqual(len(bars), 12)
        self.assertEqual(bars["2026-01"]["data-count"], "0")
        self.assertEqual(bars["2026-04"]["data-status"], "uncovered")
        self.assertNotIn("data-count", bars["2026-04"])
        self.assertEqual(float(bars["2026-03"]["height"]), 2 * float(bars["2026-02"]["height"]))
        self.assertIn("合计 9 条", "".join(root.itertext()))
        self.assertIn("A & <B>", "".join(root.itertext()))

    def test_empty_complete_year_is_valid_and_all_months_are_zero(self):
        svg = activity.render({}, 2025, dt.date(2026, 1, 1), "Empty", "ref", "all history")
        bars = [node.attrib for node in ET.fromstring(svg).iter() if "data-month" in node.attrib]
        self.assertEqual(len(bars), 12)
        self.assertTrue(all(bar["data-count"] == "0" for bar in bars))

    def test_rejects_duplicate_invalid_or_negative_statistics(self):
        for text in ("2026-01\t2\t1\n2026-01\t3\t1\n", "2026-13\t2\t1\n", "2026-01\t-2\t1\n", "2026-01\t1\t2\n", "2026-01\tx\t1\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.read(text)

    def test_rejects_data_beyond_cutoff(self):
        with self.assertRaises(ValueError):
            activity.render({"2026-12": (2, 1)}, 2026, dt.date(2026, 8, 14), "repo", "ref", "basis")


if __name__ == "__main__":
    unittest.main()
