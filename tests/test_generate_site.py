import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_site import Translator, generate  # noqa: E402
from health_check import check  # noqa: E402
from test_publish_feed import item  # noqa: E402


class GenerateTests(unittest.TestCase):
    def test_generates_schema_faq_sitemap_and_robots(self):
        content = item(publish_status="published")
        feed = {"schema_version": "0.1", "items": [content]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/listings.json").write_text(json.dumps(feed), encoding="utf-8")
            (root / "index.html").write_text("home", encoding="utf-8")
            report = generate(feed, root, ["zh"], Translator(None))
            self.assertEqual(report["generated_pages"], 1)
            page = next((root / "listings/zh").glob("*/index.html")).read_text(encoding="utf-8")
            self.assertIn('"FAQPage"', page)
            self.assertIn('"Article"', page)
            self.assertIn("translation_provider=source-fallback", page)
            self.assertIn("Sitemap:", (root / "robots.txt").read_text())
            self.assertEqual(check(root), [])

    def test_non_chinese_requires_real_translator(self):
        feed = {"schema_version": "0.1", "items": [item(publish_status="published")]}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "translator-command"):
                generate(feed, Path(directory), ["vi"], Translator(None))

    def test_removes_only_manifested_stale_pages(self):
        published = {"schema_version": "0.1", "items": [item(publish_status="published")]}
        hidden = {"schema_version": "0.1", "items": [item()]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = generate(published, root, ["zh"], Translator(None))
            page = root / report["paths"][0]
            self.assertTrue(page.exists())
            generate(hidden, root, ["zh"], Translator(None))
            self.assertFalse(page.exists())

    def test_hidden_items_do_not_generate_pages(self):
        feed = {"schema_version": "0.1", "items": [item()]}
        with tempfile.TemporaryDirectory() as directory:
            report = generate(feed, Path(directory), ["zh"], Translator(None))
            self.assertEqual(report["generated_pages"], 0)

    def test_rejects_unversioned_feed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "schema_version"):
                generate({"items": []}, Path(directory), ["zh"], Translator(None))


if __name__ == "__main__":
    unittest.main()
