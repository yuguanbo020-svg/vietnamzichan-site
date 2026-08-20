import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from publish_feed import build_feed  # noqa: E402


def item(**overrides):
    base = {
        "id": "vn-1", "country": "Vietnam", "city_region": "Hanoi",
        "category": "factory", "direction": "industrial", "title_zh": "河内厂房",
        "summary_zh": "公开招租信息", "source_platform": "example",
        "source_url": "https://example.com/post/1?utm_source=bot",
        "published_at": "2026-08-20T08:00:00+07:00",
        "collected_at": "2026-08-20T09:00:00+07:00",
        "verification_status": "已核实公开来源", "confidence": 0.91,
        "publish_status": "hidden",
    }
    base.update(overrides)
    return base


class FeedTests(unittest.TestCase):
    def test_normalizes_fields_and_keeps_human_gate(self):
        feed, report = build_feed([item()], "test-run")
        self.assertEqual(report["accepted"], 1)
        self.assertEqual(feed["task"]["human_gate"], "required_before_commit_or_deploy")
        saved = feed["items"][0]
        self.assertEqual(saved["section"], "property")
        self.assertEqual(saved["source_url"], "https://example.com/post/1")
        self.assertEqual(saved["classification"]["category"], "factory")

    def test_rejects_semantic_duplicate_and_reports_reason(self):
        duplicate = item(id="vn-2", source_url="https://mirror.example/post/9")
        feed, report = build_feed([item(), duplicate], "test-run")
        self.assertEqual(feed["count"], 1)
        self.assertIn("duplicate content", report["rejected"][0]["errors"][0])

    def test_rejects_bad_timestamp_and_confidence(self):
        _, report = build_feed([item(published_at="yesterday"), item(id="vn-2", confidence=2)])
        self.assertEqual(report["rejected_count"], 2)
        self.assertIn("ISO-8601", report["rejected"][0]["errors"][0])
        self.assertIn("0 to 1", report["rejected"][1]["errors"][0])

    def test_cli_writes_report_and_returns_one_for_partial_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            source, output, report = temp / "in.json", temp / "out.json", temp / "report.json"
            source.write_text(json.dumps([item(), {"id": "bad"}], ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "publish_feed.py"), str(source),
                 "--output", str(output), "--report", str(report), "--run-id", "smoke"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertTrue(output.exists())
            self.assertEqual(json.loads(report.read_text())["rejected_count"], 1)


if __name__ == "__main__":
    unittest.main()
