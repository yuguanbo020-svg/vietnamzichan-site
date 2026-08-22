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
            self.assertGreaterEqual(count, 50)
            for path in ("zh/index.html", "en/index.html", "vi/index.html",
                         "zh/categories/factory/index.html", "zh/cities/bac-ninh/index.html",
                         "zh/listings/index.html", "zh/contact/index.html", "zh/trust/index.html"):
                self.assertTrue((Path(folder) / path).is_file(), path)
            home = (Path(folder) / "zh/index.html").read_text(encoding="utf-8")
            self.assertIn("application/ld+json", home)
            self.assertIn("data-search", home)
            contact = (Path(folder) / "zh/contact/index.html").read_text(encoding="utf-8")
            self.assertIn('data-netlify="true"', contact)
            self.assertNotIn("OPENAI_API_KEY", "\n".join(p.read_text(encoding="utf-8") for p in Path(folder).rglob("*.*")))

    def test_css_and_js_are_local_assets(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(portal, "ROOT", Path(folder)):
            portal.build()
            page = (Path(folder) / "zh/index.html").read_text(encoding="utf-8")
            self.assertIn('/assets/site.css', page)
            self.assertIn('/assets/site.js', page)


if __name__ == "__main__":
    unittest.main()
