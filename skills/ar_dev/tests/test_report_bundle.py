"""Exercise publication inventory, fixture boundaries and both report layouts."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "scripts/check_report_bundle.py"


class ReportBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / ".gitignore").write_text("__board__/reports/*/local/\n")
        self.bundle = self.repo / "__board__/reports/v1.example"
        for directory in ("code/methods", "tables", "figures", "fixtures", "local"):
            (self.bundle / directory).mkdir(parents=True)
        (self.bundle / "v1.example.md").write_text("Report")
        (self.bundle / "metadata.json").write_text(json.dumps({
            "experiment_id": "v1.example", "created_utc": "2026-01-01",
            "protocol": {"test": True}, "provenance": {"test": True},
            "reproduction": {"test": True},
        }))
        (self.bundle / "requirements.txt").write_text("")
        (self.bundle / "code/plot.py").write_text("pass\n")
        (self.bundle / "code/methods/__init__.py").write_text("")
        (self.bundle / "code/methods/model.py").write_text("def run(): return 1\n")
        (self.bundle / "tables/result.csv").write_text("value\n1\n")
        (self.bundle / "figures/result.png").write_bytes(b"figure")
        (self.bundle / "local/raw.npy").write_bytes(b"private raw output")
        data = self.bundle / "fixtures/sample.csv"
        data.write_text("x,y\n1,0\n2,1\n")
        (self.bundle / "fixtures/manifest.json").write_text(json.dumps({
            "source": {"dataset": "public-source"}, "rows": {"indices": [0, 1]},
            "files": [{"path": "sample.csv", "sha256": hashlib.sha256(data.read_bytes()).hexdigest()}],
        }))

    def check_bundle(self, *args):
        return subprocess.run([sys.executable, str(CHECKER), str(self.bundle),
                               "--write-manifest", *args], capture_output=True, text=True)

    def test_nested_export_and_local_exclusion(self):
        export = self.root / "export"
        result = self.check_bundle("--export", str(export))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((export / "code/methods/model.py").exists())
        self.assertEqual((export / "fixtures/sample.csv").read_bytes(),
                         (self.bundle / "fixtures/sample.csv").read_bytes())
        self.assertFalse((export / "local").exists())

    def test_changed_fixture_rejected(self):
        (self.bundle / "fixtures/sample.csv").write_text("changed")
        self.assertNotEqual(self.check_bundle().returncode, 0)

    def test_unlisted_fixture_rejected(self):
        (self.bundle / "fixtures/extra.csv").write_text("x\n1\n")
        self.assertNotEqual(self.check_bundle().returncode, 0)

    def test_escaping_fixture_rejected(self):
        path = self.bundle / "fixtures/manifest.json"
        data = json.loads(path.read_text())
        data["files"][0]["path"] = "../sample.csv"
        path.write_text(json.dumps(data))
        self.assertNotEqual(self.check_bundle().returncode, 0)

    def test_fixture_budget_enforced(self):
        self.assertNotEqual(self.check_bundle("--max-fixture-mib", "0.000001").returncode, 0)

    def test_pickle_rejected(self):
        (self.bundle / "fixtures/unsafe.pkl").write_bytes(b"pickle")
        self.assertNotEqual(self.check_bundle().returncode, 0)

    def test_version_directory_report_filename(self):
        (self.bundle / "v1.example.md").rename(self.bundle / "v1.task.md")
        result = self.check_bundle("--report-file", "v1.task.md")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_same_stem_figure_csv_supported(self):
        (self.bundle / "tables/result.csv").rename(self.bundle / "figures/result.csv")
        (self.bundle / "tables").rmdir()
        result = self.check_bundle()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_report_filename_cannot_escape(self):
        self.assertNotEqual(self.check_bundle("--report-file", "../v1.example.md").returncode, 0)


if __name__ == "__main__":
    unittest.main()
