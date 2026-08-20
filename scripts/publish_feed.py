#!/usr/bin/env python3
"""Normalize, validate and publish collector content into a local feed.

This script never commits, pushes, deploys, spends money, or contacts a source.
Those actions remain explicit human gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "listings.json"
DEFAULT_REPORT = ROOT / "data" / "last_publish_report.json"
SCHEMA_VERSION = "0.1"
ALLOWED_SECTIONS = {"property", "cooperation"}
ALLOWED_SCORES = {"A", "B"}
ALLOWED_STATUSES = {"published", "hidden"}
TRACKING_KEYS = {"fbclid", "gclid", "ref", "source"}
REQUIRED_TEXT = {
    "id", "country", "city_region", "category", "direction", "title_zh",
    "summary_zh", "source_platform", "source_url", "published_at",
    "verification_status",
}


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_time(value: Any, field: str) -> str:
    text = norm(value)
    if not text:
        raise ValueError(f"{field} is required")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include timezone")
    return parsed.isoformat(timespec="seconds")


def canonical_url(value: Any) -> str:
    parts = urlsplit(norm(value))
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError("source_url must be an absolute http(s) URL")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING_KEYS]
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def infer_section(item: dict[str, Any]) -> str:
    explicit = norm(item.get("section") or item.get("content_type")).lower()
    if explicit in ALLOWED_SECTIONS:
        return explicit
    haystack = " ".join(norm(item.get(k)).lower() for k in
                        ("category", "direction", "title_zh", "summary_zh"))
    terms = ("合作", "合资", "招商", "partner", "investment", "distribution")
    return "cooperation" if any(term in haystack for term in terms) else "property"


def normalize_confidence(item: dict[str, Any]) -> tuple[float, str]:
    raw = item.get("confidence", item.get("confidence_score"))
    score = norm(item.get("score")).upper()
    if raw in (None, ""):
        raw = 0.9 if score == "A" else 0.65
    try:
        confidence = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be a number from 0 to 1") from exc
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be a number from 0 to 1")
    derived_score = score or ("A" if confidence >= 0.8 else "B")
    if derived_score not in ALLOWED_SCORES:
        raise ValueError("score must be A or B")
    return confidence, derived_score


def normalize_item(item: dict[str, Any], collected_at: str) -> dict[str, Any]:
    result = dict(item)
    for key in REQUIRED_TEXT:
        result[key] = norm(result.get(key))
    missing = sorted(key for key in REQUIRED_TEXT if not result[key])
    if missing:
        raise ValueError("missing=" + ",".join(missing))
    result["section"] = infer_section(result)
    result["publish_status"] = norm(result.get("publish_status") or "hidden").lower()
    if result["publish_status"] not in ALLOWED_STATUSES:
        raise ValueError("publish_status must be published or hidden")
    result["source_url"] = canonical_url(result["source_url"])
    result["published_at"] = parse_time(result["published_at"], "published_at")
    result["collected_at"] = parse_time(result.get("collected_at") or collected_at, "collected_at")
    result["confidence"], result["score"] = normalize_confidence(result)
    if result["score"] == "B" and result["verification_status"] != "待进一步核实":
        raise ValueError("B item must be marked 待进一步核实")
    result["content_type"] = result["section"]
    result["classification"] = {"section": result["section"], "category": result["category"],
                                "direction": result["direction"]}
    result["source"] = {"platform": result["source_platform"], "url": result["source_url"],
                        "published_at": result["published_at"], "collected_at": result["collected_at"]}
    return result


def fingerprint(item: dict[str, Any]) -> str:
    base = "|".join((item["source_url"], norm(item.get("title_zh")).casefold(),
                     norm(item.get("city_region")).casefold(),
                     norm(item.get("contact_public")).casefold()))
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def content_key(item: dict[str, Any]) -> str:
    return "|".join((norm(item.get("title_zh")).casefold(),
                     norm(item.get("city_region")).casefold(),
                     norm(item.get("category")).casefold()))


def build_feed(raw: Any, run_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    items = raw.get("items", []) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("input must be a list or an object containing items")
    collected_at = now_iso()
    accepted, rejected = [], []
    seen_fingerprints, seen_content, seen_ids = set(), set(), set()
    for index, candidate in enumerate(items):
        if not isinstance(candidate, dict):
            rejected.append({"index": index, "reason_code": "invalid_type", "errors": ["not an object"]})
            continue
        try:
            item = normalize_item(candidate, collected_at)
            fp, key = fingerprint(item), content_key(item)
            errors = []
            if item["id"] in seen_ids:
                errors.append("duplicate id")
            if fp in seen_fingerprints or key in seen_content:
                errors.append("duplicate content")
            if errors:
                raise ValueError("; ".join(errors))
            item["fingerprint"] = fp
            accepted.append(item)
            seen_ids.add(item["id"])
            seen_fingerprints.add(fp)
            seen_content.add(key)
        except (TypeError, ValueError) as exc:
            rejected.append({"index": index, "id": candidate.get("id"),
                             "reason_code": "validation_failed", "errors": [str(exc)]})
    accepted.sort(key=lambda item: (item["score"] != "A", item["published_at"]))
    task = {"run_id": run_id or f"feed-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            "stage": "normalized", "human_gate": "required_before_commit_or_deploy"}
    feed = {"schema_version": SCHEMA_VERSION, "updated_at": collected_at, "task": task,
            "count": len(accepted), "rejected_count": len(rejected), "items": accepted}
    report = {"schema_version": SCHEMA_VERSION, "run_id": task["run_id"],
              "accepted": len(accepted), "rejected_count": len(rejected), "rejected": rejected}
    return feed, report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--run-id")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        feed, report = build_feed(raw, args.run_id)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"fatal: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"run_id={report['run_id']} accepted={report['accepted']} "
          f"rejected={report['rejected_count']} output={args.output}")
    return 0 if not report["rejected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
