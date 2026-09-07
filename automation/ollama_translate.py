#!/usr/bin/env python3
"""Translator adapter for scripts/generate_site.py's --translator-command hook.

scripts/generate_site.py already knows how to call an external local-model command:
it writes {"language": "vi"|"en", "fields": {"title","summary","faq_question","faq_answer"}}
to this script's stdin and expects {"fields": {...same 4 keys, translated...}} on stdout.

Usage (wired up by automation/listing_publisher.py):
  python3 scripts/generate_site.py --languages zh,vi,en \
      --translator-command "python3 automation/ollama_translate.py"

Env vars (automation/.env):
  OLLAMA_HOST   default http://localhost:11434
  OLLAMA_MODEL  default qwen2.5:7b-instruct
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LANG_NAMES = {"vi": "Vietnamese", "en": "English"}


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def ollama_chat(host: str, model: str, prompt: str, timeout: int = 90) -> str:
    url = host.rstrip("/") + "/api/chat"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = json.loads(resp.read())
    return raw.get("message", {}).get("content", "")


def extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text.strip(), re.S)
    if not m:
        raise ValueError("model did not return JSON")
    return json.loads(m.group(0))


def main() -> int:
    load_dotenv(ROOT / "automation" / ".env")
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    payload = json.loads(sys.stdin.read())
    language = payload["language"]
    fields = payload["fields"]
    lang_name = LANG_NAMES.get(language, language)

    prompt = f"""Translate the following fields from Chinese to {lang_name}. Keep the meaning exact,
natural for a real-estate/industrial-property website, no explanations. Output STRICT JSON only,
with exactly these 4 keys: title, summary, faq_question, faq_answer.

title: {fields.get('title','')}
summary: {fields.get('summary','')}
faq_question: {fields.get('faq_question','')}
faq_answer: {fields.get('faq_answer','')}
"""
    try:
        reply = ollama_chat(host, model, prompt)
        translated = extract_json(reply)
        out_fields = {k: str(translated.get(k, "")).strip() for k in ("title", "summary", "faq_question", "faq_answer")}
        if not all(out_fields.values()):
            raise ValueError("translation missing one or more fields")
    except (urllib.error.URLError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    print(json.dumps({"fields": out_fields}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
