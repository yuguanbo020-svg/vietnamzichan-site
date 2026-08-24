import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class NewsPrivatePipelineTests(unittest.TestCase):
    def test_generated_news_is_traceable_and_separated(self):
        data=json.loads((ROOT/"data/news_private_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["model"],"qwen3-coder:30b")
        self.assertEqual(len(data["items"]),3)
        for item in data["items"]:
            page=(ROOT/"news"/item["slug"]/"index.html").read_text(encoding="utf-8")
            self.assertIn(item["source_url"],page)
            self.assertIn("来源事实",page)
            self.assertIn("本地AI团队讨论",page)
            self.assertIn("情景推演（不是事实）",page)
            self.assertIn(item["image"],page)
    def test_index_links_articles_and_images(self):
        page=(ROOT/"news/index.html").read_text(encoding="utf-8")
        data=json.loads((ROOT/"data/news_private_analysis.json").read_text(encoding="utf-8"))
        for item in data["items"]:
            self.assertIn(f'/news/{item["slug"]}/',page)
            self.assertIn(item["image"],page)

if __name__=="__main__": unittest.main()
