#!/usr/bin/env python3
"""Listing Desk v1 — publisher (runs on the Owner's own machine, not in CI/cloud).

Takes APPROVED listing_submissions, turns them into feed items compatible with the
site's existing data/listings.json schema, reuses the EXISTING static generator
(scripts/generate_site.py) to build real, indexable /listings/{lang}/{slug}/ pages
and refresh sitemap.xml/robots.txt, commits, and pushes to main using your own git
credentials (this script does not create or use any GitHub token). After a
successful push it marks the rows PUBLISHED with their real public URLs.

This intentionally reuses build_portal.py's sibling generator instead of writing a
new template from scratch (automation/README.md: "Reuse existing portal/
build_portal.py, feed normalizer and generator; do not rebuild from zero.").

Env vars (automation/.env, not committed):
  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY   same as listing_ai_worker.py
  SITE_URL              default https://vietnamzichan.com
  GIT_PUSH              default "1" — set to "0" to commit locally without pushing
                         (useful for a first dry run / manual review before going live)

Requires: your own `git` to already be authenticated for this repo on this machine
(push access to yuguanbo020-svg/vietnamzichan-site). This script never creates a
GitHub token and never touches repo permissions.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "automation" / "logs"
SITE = "vietnamzichan"
FEED_PATH = ROOT / "data" / "listings.json"

CITY_LABELS_ZH = {
    "ho-chi-minh-city": "胡志明市", "binh-duong": "平阳", "dong-nai": "同奈",
    "hanoi": "河内", "bac-ninh": "北宁", "hai-phong": "海防", "da-nang": "岘港",
}
CATEGORY_LABELS_ZH = {
    "factory": "厂房", "industrial-land": "工业土地", "warehouse": "仓库物流",
    "hotel": "酒店商业", "residential": "住宅", "agriculture": "农业",
}
DIRECTION_LABELS_ZH = {"sell": "出售", "rent": "出租", "buy": "求购", "lease": "求租", "cooperation": "找合作"}


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def log(event: str, **fields) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, **fields}
    line = json.dumps(record, ensure_ascii=False)
    print(line, file=sys.stderr)
    with (LOG_DIR / "listing_publisher.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def http_json(method: str, url: str, headers: dict, body: dict | None = None, timeout: int = 60):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} {method} {url}: {exc.read().decode('utf-8', 'ignore')[:500]}") from exc


class Supabase:
    def __init__(self, url: str, service_key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }

    def select_approved(self, limit: int = 100):
        url = f"{self.base}/listing_submissions?site=eq.{SITE}&status=eq.APPROVED&order=created_at.asc&limit={limit}"
        return http_json("GET", url, self.headers) or []

    def update(self, row_id: str, patch: dict):
        url = f"{self.base}/listing_submissions?id=eq.{row_id}"
        headers = {**self.headers, "Prefer": "return=minimal"}
        http_json("PATCH", url, headers, patch)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug_for(row: dict) -> str:
    # Already URL-safe (hex uuid fragment) so slugify() in generate_site.py is a no-op —
    # this keeps scripts/health_check.py's id<->page-path check happy.
    return "ld-" + str(row["id"]).replace("-", "")[:10]


def build_feed_item(row: dict, site_url: str) -> dict:
    ai = row.get("ai") or {}
    listing_type = row["listing_type"]
    city = row.get("city_region") or "vietnam"
    category = row.get("category") or "other"
    slug = slug_for(row)
    staff = row.get("submitter_role") == "staff"
    zh_url = f"{site_url}/listings/zh/{slug}/"
    return {
        "id": slug,
        "country": "越南",
        "city_region": CITY_LABELS_ZH.get(city, city),
        "category": CATEGORY_LABELS_ZH.get(category, category),
        "direction": DIRECTION_LABELS_ZH.get(listing_type, listing_type),
        "title_zh": ai.get("title_zh") or (row.get("raw_text") or "")[:30],
        "summary_zh": ai.get("summary_zh") or (row.get("raw_text") or "")[:150],
        "source_platform": "VietnamZiChan Listing Desk",
        "source_url": zh_url,
        "published_at": now_iso(),
        "collected_at": row.get("created_at") or now_iso(),
        "verification_status": "员工已审核" if staff else "用户自报，员工已审核通过",
        "score": "A" if staff else "B",
        "confidence": 0.9 if staff else 0.75,
        "section": "cooperation" if listing_type == "cooperation" else "property",
        "publish_status": "published",
        "_submission_id": row["id"],  # kept only in our local feed for traceability; harmless extra key
    }


def load_feed() -> dict:
    if FEED_PATH.is_file():
        return json.loads(FEED_PATH.read_text(encoding="utf-8"))
    return {"schema_version": "0.1", "updated_at": now_iso(), "count": 0, "rejected_count": 0, "items": []}


def save_feed(feed: dict) -> None:
    feed["updated_at"] = now_iso()
    feed["count"] = len(feed["items"])
    FEED_PATH.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def keep_deploy_manifest_zh_only() -> None:
    """Keep .factory-generated.json limited to zh pages before committing.

    Cloudflare Pages rebuilds this static site without local Ollama and therefore
    regenerates listing pages only for zh (mirroring the factory workflow). If the
    committed manifest also listed vi/en pages, that zh-only rebuild would treat the
    committed vi/en pages as stale and delete them from the deployment. vi/en pages
    are committed artifacts and must be preserved as-is.
    """
    manifest_path = ROOT / ".factory-generated.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["paths"] = [p for p in manifest.get("paths", []) if p.startswith("listings/zh/")]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    log("run", cmd=" ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False, **kw)


def main() -> int:
    load_dotenv(ROOT / "automation" / ".env")
    url = env("SUPABASE_URL")
    key = env("SUPABASE_SERVICE_ROLE_KEY")
    site_url = env("SITE_URL", "https://vietnamzichan.com")
    do_push = env("GIT_PUSH", "1") != "0"
    if not url or not key:
        log("config_error", reason="SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing — see automation/.env.example")
        return 1

    sb = Supabase(url, key)
    try:
        rows = sb.select_approved()
    except Exception as exc:  # noqa: BLE001
        log("fetch_failed", error=str(exc))
        return 1

    if not rows:
        log("nothing_to_publish")
        print(json.dumps({"published": 0}, ensure_ascii=False))
        return 0

    feed = load_feed()
    existing_ids = {it["id"] for it in feed["items"]}
    new_items, slugs_by_submission = [], {}
    for row in rows:
        item = build_feed_item(row, site_url)
        if item["id"] in existing_ids:
            item["id"] = item["id"] + "x"  # extremely unlikely collision guard
        new_items.append(item)
        slugs_by_submission[row["id"]] = item["id"]

    feed["items"].extend(new_items)
    save_feed(feed)
    log("feed_updated", added=len(new_items))

    gen = run([sys.executable, "scripts/generate_site.py", "--feed", "data/listings.json",
               "--output", ".", "--languages", "zh,vi,en",
               "--translator-command", f"{sys.executable} automation/ollama_translate.py"])
    if gen.returncode != 0:
        log("generate_failed", stdout=gen.stdout[-2000:], stderr=gen.stderr[-2000:])
        return 1
    log("generate_ok", stdout=gen.stdout[-500:])

    health = run([sys.executable, "scripts/health_check.py"])
    log("health_check", stdout=health.stdout.strip())
    if health.returncode != 0:
        log("health_check_failed", detail=health.stdout.strip())
        return 1

    keep_deploy_manifest_zh_only()
    paths_to_add = ["data/listings.json", "sitemap.xml", "robots.txt"]
    if (ROOT / ".factory-generated.json").is_file():
        paths_to_add.append(".factory-generated.json")
    paths_to_add.append("listings")
    run(["git", "add", *paths_to_add])
    commit_msg = (
        f"feat(listing-desk): publish {len(new_items)} approved listing(s) [automated]\n\n"
        "Generated by automation/listing_publisher.py — local Ollama pipeline, "
        "reuses scripts/generate_site.py. Not an interactive Claude session change."
    )
    commit = run(["git", "commit", "-m", commit_msg])
    if commit.returncode != 0:
        log("commit_failed", stdout=commit.stdout, stderr=commit.stderr)
        return 1
    log("commit_ok", stdout=commit.stdout.strip())

    if do_push:
        push = run(["git", "push", "origin", "HEAD:main"])
        if push.returncode != 0:
            log("push_failed", stdout=push.stdout, stderr=push.stderr,
                hint="git push failed — make sure this machine has its own push access "
                     "to yuguanbo020-svg/vietnamzichan-site (no token is created by this script).")
            return 1
        log("push_ok")
    else:
        log("push_skipped", reason="GIT_PUSH=0")

    if do_push:
        for row in rows:
            slug = slugs_by_submission[row["id"]]
            urls = {lang: f"{site_url}/listings/{lang}/{slug}/" for lang in ("zh", "vi", "en")}
            try:
                sb.update(row["id"], {
                    "status": "PUBLISHED",
                    "published_slug": slug,
                    "published_url": urls["zh"],
                    "published_at": now_iso(),
                })
                log("marked_published", id=row["id"], slug=slug)
            except Exception as exc:  # noqa: BLE001
                log("mark_published_failed", id=row["id"], error=str(exc))

    print(json.dumps({"published": len(new_items) if do_push else 0,
                       "committed_not_pushed": 0 if do_push else len(new_items)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
