#!/usr/bin/env python3
"""Fail fast when the generated site or normalized feed is unhealthy."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(root: Path = ROOT) -> list[str]:
    failures = []
    for relative in ("index.html", "robots.txt", "sitemap.xml", "data/listings.json"):
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"missing_or_empty:{relative}")
    if (root / ".portal-built.json").is_file():
        for relative in ("zh/index.html", "en/index.html", "vi/index.html", "zh/listings/index.html",
                         "zh/contact/index.html", "zh/trust/index.html", "assets/site.css", "assets/site.js"):
            if not (root / relative).is_file():
                failures.append(f"missing_portal_page:{relative}")
        try:
            sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
            for url in ("/zh/", "/en/", "/vi/", "/zh/categories/factory/", "/zh/cities/bac-ninh/"):
                if url not in sitemap:
                    failures.append(f"missing_sitemap_url:{url}")
        except OSError as exc:
            failures.append(f"invalid_sitemap:{exc}")
    try:
        feed = json.loads((root / "data/listings.json").read_text(encoding="utf-8"))
        if feed.get("schema_version") != "0.1":
            failures.append("invalid_schema_version:data/listings.json")
        for item in feed.get("items", []):
            if item.get("publish_status") == "published":
                marker = f"/{item['id'].casefold()}/index.html"
                if not any(marker in str(path).casefold() for path in (root / "listings").glob("*/*/index.html")):
                    failures.append(f"missing_page:{item['id']}")
    except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        failures.append(f"invalid_feed:{type(exc).__name__}:{exc}")
    return failures


if __name__ == "__main__":
    problems = check()
    print(json.dumps({"status": "fail" if problems else "ok", "failures": problems}, ensure_ascii=False))
    raise SystemExit(1 if problems else 0)
