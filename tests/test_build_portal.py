import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.build_portal as portal


class PortalBuildTests(unittest.TestCase):
    def test_builds_complete_portal_without_cloud_dependency(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(portal, "ROOT", Path(folder)):
            count = portal.build()
            self.assertGreaterEqual(count, 100)
            for path in ("zh/index.html", "en/index.html", "vi/index.html",
                         "zh/categories/factory/index.html", "zh/cities/bac-ninh/index.html",
                         "zh/listings/index.html", "zh/contact/index.html", "zh/trust/index.html"):
                self.assertTrue((Path(folder) / path).is_file(), path)
            for path in ("vi/market/index.html", "zh/market/index.html",
                         "vi/market/bac-ninh/factory-for-rent/index.html",
                         "zh/market/binh-duong/industrial-land/index.html"):
                self.assertTrue((Path(folder) / path).is_file(), path)
            root = (Path(folder) / "index.html").read_text(encoding="utf-8")
            self.assertIn("url=/vi/", root)
            self.assertNotIn("url=/zh/", root)
            home = (Path(folder) / "zh/index.html").read_text(encoding="utf-8")
            self.assertIn("application/ld+json", home)
            self.assertIn("data-search", home)
            contact = (Path(folder) / "zh/contact/index.html").read_text(encoding="utf-8")
            self.assertIn('data-netlify="true"', contact)
            vi_market = (Path(folder) / "vi/market/bac-ninh/factory-for-rent/index.html").read_text(encoding="utf-8")
            self.assertIn("Nhà xưởng cho thuê tại Bắc Ninh", vi_market)
            zh_market = (Path(folder) / "zh/market/bac-ninh/factory-for-rent/index.html").read_text(encoding="utf-8")
            self.assertIn("北宁厂房出租", zh_market)
            self.assertNotIn("OPENAI_API_KEY", "\n".join(p.read_text(encoding="utf-8") for p in Path(folder).rglob("*.*")))

    def test_css_and_js_are_local_assets(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(portal, "ROOT", Path(folder)):
            portal.build()
            page = (Path(folder) / "zh/index.html").read_text(encoding="utf-8")
            self.assertIn('/assets/site.css', page)
            self.assertIn('/assets/site.js', page)


if __name__ == "__main__":
    unittest.main()
