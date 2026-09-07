#!/usr/bin/env python3
"""Listing Desk v1 — private AI worker (runs on the Owner's own machine, not in CI/cloud).

Polls Supabase for RAW listing_submissions (site=vietnamzichan), asks a local Ollama
model to classify / detect missing fields / clean up into a canonical Chinese
title+summary / suggest keywords & image alt text / give a dedupe hint, then moves
each row to PENDING_REVIEW (ready for staff) or NEEDS_INFO (missing required fields).

This script never commits, pushes, deploys, spends money, or contacts a source.
It only talks to your own Supabase project (service role key) and your own local
Ollama server. Nothing here depends on Claude / ChatGPT / Codex at runtime.

Env vars (put them in automation/.env, which must NOT be committed):
  SUPABASE_URL                 e.g. https://rpfccljejzfixohgwtpr.supabase.co
  SUPABASE_SERVICE_ROLE_KEY    Settings > API > service_role (bypasses RLS — keep local only)
  OLLAMA_HOST                  default http://localhost:11434
  OLLAMA_MODEL                 default qwen2.5:7b-instruct (override to whatever you've pulled)

Suggested cron (see automation/listing_desk_cron.sh for the full daily chain):
  0 10,17 * * * cd /path/to/vietnamzichan-site && ./automation/listing_desk_cron.sh >> automation/logs/cron.log 2>&1
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "automation" / "logs"
SITE = "vietnamzichan"

REQUIRED_FOR_PUBLISH = ("city_region", "category", "contact_text")
CATEGORIES = ["factory", "industrial-land", "warehouse", "hotel", "residential", "agriculture"]
CITIES = ["ho-chi-minh-city", "binh-duong", "dong-nai", "hanoi", "bac-ninh", "hai-phong", "da-nang"]


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
    with (LOG_DIR / "listing_ai_worker.log").open("a", encoding="utf-8") as f:
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

    def select_raw(self, limit: int = 20):
        url = f"{self.base}/listing_submissions?site=eq.{SITE}&status=eq.RAW&order=created_at.asc&limit={limit}"
        return http_json("GET", url, self.headers) or []

    def update(self, row_id: str, patch: dict):
        url = f"{self.base}/listing_submissions?id=eq.{row_id}"
        headers = {**self.headers, "Prefer": "return=minimal"}
        http_json("PATCH", url, headers, patch)


def ollama_chat(host: str, model: str, prompt: str, timeout: int = 120) -> str:
    url = host.rstrip("/") + "/api/chat"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.2},
    }
    resp = http_json("POST", url, {"Content-Type": "application/json"}, body, timeout=timeout)
    return (resp or {}).get("message", {}).get("content", "")


def build_prompt(row: dict) -> str:
    return f"""你是 VietnamZiChan 网站的房源信息整理助手。下面是一条用户/员工提交的原始信息（可能混杂中文/越南语/英语），
请你输出【严格的 JSON】（不要任何解释文字，不要markdown代码块），字段如下：
{{
  "title_zh": "一句话中文标题，不超过30字",
  "title_vi": "越南语标题",
  "title_en": "English title",
  "summary_zh": "中文摘要，2-4句，包含面积/位置/价格/类型等关键信息",
  "summary_vi": "越南语摘要",
  "summary_en": "English summary",
  "detected_city": "从这些值里选一个最接近的，选不出来就填 null：{CITIES}",
  "detected_category": "从这些值里选一个最接近的，选不出来就填 null：{CATEGORIES}",
  "keywords_zh": ["中文关键词", "..."],
  "alt_texts": ["每张图片一句中文alt文字（如果没有图片就给空数组）"],
  "missing_fields": ["缺少的关键信息，从 city_region/category/contact_text/area_text/price_text 里选，都齐全就给空数组"],
  "dedupe_hint": "用于判断是否与已有房源重复的一小段指纹文字（城市+类别+面积+价格的简短组合）"
}}

原始信息：
类型：{row.get('listing_type')}
城市（用户填写）：{row.get('city_region') or '(未填)'}
类别（用户填写）：{row.get('category') or '(未填)'}
价格：{row.get('price_text') or '(未填)'}
面积：{row.get('area_text') or '(未填)'}
联系方式：{row.get('contact_text') or '(未填)'}
详细描述：
{row.get('raw_text')}
"""


def extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("model did not return JSON")
    return json.loads(m.group(0))


def process_row(sb: Supabase, host: str, model: str, row: dict) -> None:
    row_id = row["id"]
    prompt = build_prompt(row)
    raw_reply = ollama_chat(host, model, prompt)
    ai = extract_json(raw_reply)

    # Fill in city/category if the user left them blank and the model detected one.
    city = row.get("city_region") or ai.get("detected_city")
    category = row.get("category") or ai.get("detected_category")

    missing = []
    if not city:
        missing.append("city_region")
    if not category:
        missing.append("category")
    if not row.get("contact_text") and "联系" not in (row.get("raw_text") or "") and "contact" not in (row.get("raw_text") or "").lower():
        missing.append("contact_text")
    model_missing = ai.get("missing_fields") or []
    for m in model_missing:
        if m not in missing:
            missing.append(m)
    ai["missing_fields"] = missing

    # Step 1: RAW -> AI_PROCESSED (persist the AI output for the audit trail).
    sb.update(row_id, {
        "status": "AI_PROCESSED",
        "ai": ai,
        "city_region": city,
        "category": category,
    })

    # Step 2: AI_PROCESSED -> PENDING_REVIEW (ready for staff) or NEEDS_INFO.
    next_status = "NEEDS_INFO" if missing else "PENDING_REVIEW"
    sb.update(row_id, {"status": next_status})
    log("processed", id=row_id, next_status=next_status, missing=missing)


def main() -> int:
    load_dotenv(ROOT / "automation" / ".env")
    url = env("SUPABASE_URL")
    key = env("SUPABASE_SERVICE_ROLE_KEY")
    host = env("OLLAMA_HOST", "http://localhost:11434")
    model = env("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    if not url or not key:
        log("config_error", reason="SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing — see automation/.env.example")
        return 1

    sb = Supabase(url, key)
    try:
        rows = sb.select_raw()
    except Exception as exc:  # noqa: BLE001
        log("fetch_failed", error=str(exc))
        return 1

    log("batch_start", count=len(rows))
    ok, failed = 0, 0
    for row in rows:
        try:
            process_row(sb, host, model, row)
            ok += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            log("process_failed", id=row.get("id"), error=str(exc))
        time.sleep(0.5)
    log("batch_done", ok=ok, failed=failed)
    print(json.dumps({"ok": ok, "failed": failed, "total": len(rows)}, ensure_ascii=False))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
