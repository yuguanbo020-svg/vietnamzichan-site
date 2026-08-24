import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MultilingualNewsTests(unittest.TestCase):
    def test_default_is_vietnamese_and_all_languages_exist(self):
        self.assertIn('lang="vi"',(ROOT/"news/index.html").read_text(encoding="utf-8"))
        for lang in ("vi","zh","en"):
            root=ROOT/"news" if lang=="vi" else ROOT/lang/"news"
            page=(root/"index.html").read_text(encoding="utf-8")
            self.assertIn('href="/news/">VI',page)
            self.assertIn('href="/zh/news/">中文',page)
            self.assertIn('href="/en/news/">EN',page)
    def test_articles_have_decision_sections_without_repeated_ai_team(self):
        data=json.loads((ROOT/"data/news_multilingual.json").read_text(encoding="utf-8"))
        for lang in ("vi","zh","en"):
            root=ROOT/"news" if lang=="vi" else ROOT/lang/"news"
            for item in data["items"]:
                page=(root/item["slug"]/"index.html").read_text(encoding="utf-8")
                self.assertIn(item["source_url"],page)
                self.assertNotIn("AI团队讨论",page)
                self.assertLessEqual(page.lower().count("private model"),1)
if __name__=="__main__": unittest.main()
