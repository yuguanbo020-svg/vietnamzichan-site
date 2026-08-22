#!/usr/bin/env python3
"""Generate static, search-friendly pages from the normalized content feed."""
from __future__ import annotations

import argparse
import html
import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://vietnamzichan.com"
LANGUAGES = {"zh": "zh-CN", "vi": "vi-VN", "en": "en"}


def slugify(value: str) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return ascii_slug or "item"


def log(event: str, **fields: Any) -> None:
    record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "event": event, **fields}
    print(json.dumps(record, ensure_ascii=False), file=sys.stderr)


@dataclass
class Translation:
    title: str
    summary: str
    faq_question: str
    faq_answer: str
    provider: str


class Translator:
    """Local-model adapter. The command receives JSON on stdin and returns JSON."""

    def __init__(self, command: str | None, retries: int = 2, timeout: int = 45):
        self.command = shlex.split(command) if command else None
        self.retries = retries
        self.timeout = timeout

    def translate(self, item: dict[str, Any], language: str) -> Translation:
        question = f"这条{item['category']}信息的来源和核实状态是什么？"
        answer = (f"来源为{item['source_platform']}，发布时间为{item['published_at']}，"
                  f"当前状态：{item['verification_status']}。交易前请向原发布方复核。")
        fallback = Translation(item["title_zh"], item["summary_zh"], question, answer, "source-fallback")
        if language == "zh":
            return fallback
        if not self.command:
            raise RuntimeError(f"language {language} requires --translator-command")
        payload = {"language": language, "fields": {"title": item["title_zh"],
                   "summary": item["summary_zh"], "faq_question": question, "faq_answer": answer}}
        last_error = "unknown error"
        for attempt in range(1, self.retries + 2):
            try:
                result = subprocess.run(self.command, input=json.dumps(payload, ensure_ascii=False),
                                        capture_output=True, text=True, timeout=self.timeout, check=False)
                if result.returncode:
                    raise RuntimeError(f"exit={result.returncode}: {result.stderr.strip()}")
                translated = json.loads(result.stdout)
                fields = translated.get("fields", translated)
                values = [str(fields.get(key, "")).strip() for key in
                          ("title", "summary", "faq_question", "faq_answer")]
                if not all(values):
                    raise ValueError("model response is missing translated fields")
                return Translation(*values, provider="local-command")
            except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, RuntimeError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                log("translation_retry", item_id=item["id"], language=language,
                    attempt=attempt, max_attempts=self.retries + 1, reason=last_error)
                if attempt <= self.retries:
                    time.sleep(min(attempt, 2))
        raise RuntimeError(f"translation failed for {item['id']}/{language}: {last_error}")


def keywords(item: dict[str, Any], language: str) -> list[str]:
    base = [item["country"], item["city_region"], item["category"], item["direction"]]
    intent = {"zh": ["越南投资", "价格与来源", "合作机会"],
              "vi": ["đầu tư Việt Nam", "giá và nguồn", "cơ hội hợp tác"],
              "en": ["Vietnam investment", "price and source", "cooperation opportunity"]}[language]
    return [" ".join(filter(None, (base[1], base[2], term))) for term in intent]


def render_page(item: dict[str, Any], language: str, translation: Translation, canonical: str) -> str:
    title = html.escape(translation.title)
    summary = html.escape(translation.summary)
    keyphrases = keywords(item, language)
    description = html.escape((translation.summary[:150] + " — " + keyphrases[0])[:180], quote=True)
    schema = {
        "@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": translation.title, "description": translation.summary,
             "datePublished": item["published_at"], "dateModified": item["collected_at"],
             "inLanguage": LANGUAGES[language], "mainEntityOfPage": canonical,
             "isBasedOn": item["source_url"], "author": {"@type": "Organization", "name": "VietnamZiChan"}},
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": translation.faq_question,
             "acceptedAnswer": {"@type": "Answer", "text": translation.faq_answer}}]},
        ]}
    return f'''<!doctype html>
<html lang="{LANGUAGES[language]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | VietnamZiChan</title><meta name="description" content="{description}">
<meta name="keywords" content="{html.escape(', '.join(keyphrases), quote=True)}"><link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{description}"><meta property="og:url" content="{canonical}">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False).replace('</', '<\\/')}</script>
<style>body{{font:16px/1.7 system-ui;max-width:760px;margin:auto;padding:28px;color:#17211f}}a{{color:#0b6d61}}.meta{{color:#66736f}}.notice{{background:#fff4d8;padding:12px;border-radius:8px}}</style></head>
<body><nav><a href="/">VietnamZiChan</a></nav><main><h1>{title}</h1>
<p class="meta">{html.escape(item['city_region'])} · {html.escape(item['category'])} · {html.escape(item['published_at'])}</p>
<p>{summary}</p><h2>{html.escape(translation.faq_question)}</h2><p>{html.escape(translation.faq_answer)}</p>
<p class="notice">自动整理内容，置信度 {item['confidence']:.0%}。不构成交易、投资或法律建议。</p>
<p>原始来源：<a href="{html.escape(item['source_url'], quote=True)}" rel="nofollow noopener">{html.escape(item['source_platform'])}</a></p>
</main><footer><small>translation_provider={translation.provider}</small></footer></body></html>'''


def generate(feed: dict[str, Any], output: Path, languages: list[str], translator: Translator) -> dict[str, Any]:
    if feed.get("schema_version") != "0.1" or not isinstance(feed.get("items"), list):
        raise ValueError("feed must use schema_version 0.1 and contain items")
    manifest_path = output / ".factory-generated.json"
    previous = []
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8")).get("paths", [])
        except (OSError, json.JSONDecodeError, AttributeError):
            log("stale_cleanup_skipped", reason="invalid previous manifest")
    written, urls = [], [SITE_URL + "/"]
    for item in feed["items"]:
        if item.get("publish_status") != "published":
            continue
        # IDs are unique after normalization and make stable URLs even when titles change.
        slug = slugify(item["id"])
        for language in languages:
            translated = translator.translate(item, language)
            relative = Path("listings") / language / slug / "index.html"
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            url = f"{SITE_URL}/{relative.parent.as_posix()}/"
            target.write_text(render_page(item, language, translated, url) + "\n", encoding="utf-8")
            written.append(str(relative)); urls.append(url)
            log("page_generated", item_id=item["id"], language=language, path=str(relative),
                provider=translated.provider)
    sitemap_path = output / "sitemap.xml"
    portal_urls = []
    if sitemap_path.exists():
        portal_urls = re.findall(r"<loc>([^<]+)</loc>", sitemap_path.read_text(encoding="utf-8"))
    all_urls = list(dict.fromkeys(portal_urls + urls))
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
              "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in all_urls) + "\n</urlset>\n"
    sitemap_path.write_text(sitemap, encoding="utf-8")
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    for relative in sorted(set(previous) - set(written)):
        candidate = (output / relative).resolve()
        listings_root = (output / "listings").resolve()
        if candidate.name == "index.html" and listings_root in candidate.parents and candidate.is_file():
            candidate.unlink()
            log("stale_page_removed", path=relative)
    manifest_path.write_text(json.dumps({"schema_version": "0.1", "paths": written},
                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"generated_pages": len(written), "paths": written, "urls": urls}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed", type=Path, default=ROOT / "data" / "listings.json")
    parser.add_argument("--output", type=Path, default=ROOT)
    parser.add_argument("--languages", default="zh")
    parser.add_argument("--translator-command")
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args(argv)
    languages = [part.strip() for part in args.languages.split(",") if part.strip()]
    invalid = sorted(set(languages) - LANGUAGES.keys())
    if invalid:
        print(f"fatal: unsupported languages: {','.join(invalid)}", file=sys.stderr); return 2
    try:
        feed = json.loads(args.feed.read_text(encoding="utf-8"))
        report = generate(feed, args.output, languages,
                          Translator(args.translator_command, retries=max(args.retries, 0)))
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        log("generation_failed", reason=f"{type(exc).__name__}: {exc}")
        return 1
    log("generation_complete", **report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
