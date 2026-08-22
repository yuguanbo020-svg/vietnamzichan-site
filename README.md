# VietnamZiChan 越南资产网

Domain: vietnamzichan.com
Netlify Site ID: ecb4a907-4fda-43c0-b574-0f6b792ce1c2

## Carbon Website Factory V0.1

Normalize an aigod collector result without publishing it:

```sh
python3 scripts/publish_feed.py cleaned_items.json
```

The command validates timestamps and confidence, classifies missing sections,
removes tracking parameters, rejects duplicate IDs/content, and writes a
machine-readable failure report. Output defaults to `hidden`; commit, push and
deployment remain manual gates. See `docs/content-contract-v0.1.md`.

Run the minimum smoke suite with:

```sh
python3 -m unittest discover -s tests -v
```

Build the complete portal before generating approved feed detail pages:

```sh
python3 scripts/build_portal.py
python3 scripts/generate_site.py --languages zh
python3 scripts/health_check.py
```

The portal build is deterministic and uses only the Python standard library. It
does not require Codex, OpenAI, a cloud model, an API key, or network access at
runtime. AI matching is a reserved interface only; current search is local,
feed-backed filtering. Netlify detects the inquiry form during deployment.

Generate static SEO/AEO pages after human approval changes items to
`publish_status: published`:

```sh
python3 scripts/generate_site.py --languages zh
python3 scripts/health_check.py
```

For `vi` or `en`, a local model command can be connected without adding an API
key. It receives JSON on stdin and must return the translated `fields` as JSON:

```sh
python3 scripts/generate_site.py --languages zh,vi,en \
  --translator-command '/path/to/local-translator'
```

Translation failures are retried and logged as structured JSON. Generated pages
include long-tail keywords, FAQ, Article/FAQ schema, canonical metadata, source
attribution and confidence notices. The workflow only uploads a review artifact;
it cannot commit or deploy. Non-Chinese generation fails closed when no real
translator is configured, preventing Chinese fallback text from being mislabeled.
