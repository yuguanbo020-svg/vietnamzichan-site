import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class NewsPrivatePipelineTests(unittest.TestCase):
    def test_generated_news_is_traceable_and_multilingual(self):
        data=json.loads((ROOT/"data/news_multilingual.json").read_text(encoding="utf-8"))
        self.assertEqual(data["model"],"qwen3-coder:30b")
        self.assertEqual(len(data["items"]),3)
        for item in data["items"]:
            for lang,heading in (("vi","Thông tin từ nguồn"),("zh","来源事实"),("en","Source facts")):
                root=ROOT/"news" if lang=="vi" else ROOT/lang/"news"
                page=(root/item["slug"]/"index.html").read_text(encoding="utf-8")
                self.assertIn(item["source_url"],page)
                self.assertIn(heading,page)
                self.assertIn(item["image"],page)
                self.assertNotIn("本地AI团队讨论",page)
    def test_index_links_articles_and_images(self):
        data=json.loads((ROOT/"data/news_multilingual.json").read_text(encoding="utf-8"))
        for lang in ("vi","zh","en"):
            root=ROOT/"news" if lang=="vi" else ROOT/lang/"news"
            page=(root/"index.html").read_text(encoding="utf-8")
            for item in data["items"]:
                prefix="" if lang=="vi" else f"/{lang}"
                self.assertIn(f'{prefix}/news/{item["slug"]}/',page)
                self.assertIn(item["image"],page)

if __name__=="__main__": unittest.main()
