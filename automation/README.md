# VietnamZiChan Private Website Operator

Default production chain:

Owner direction -> Jan -> Carbon Council -> local queue -> OpenHands + qwen3-coder:30b -> tests -> Judge -> staging/deploy candidate -> OpenClaw/browser operations -> local metrics -> next queue item.

Rules:

- Codex and cloud AI are not default runtime dependencies.
- Keep project state, logs, results and failures locally.
- Reuse existing portal/build_portal.py, feed normalizer and generator; do not rebuild from zero.
- When a page is incomplete, queue a concrete improvement task instead of repeatedly producing scan reports.
- No verified listing data means show an honest empty state; never fabricate inventory.
- Prioritize site maturity, search keywords, indexable city/category pages, inquiry conversion and real user feedback.
- Failed tasks are recorded and re-queued with the failure reason.
- Payment, identity declaration, OTP/CAPTCHA, biometric and final sensitive submission remain human gates.

Machine-readable queue: `automation/private-site-operator.json`.

## Listing Desk v1

User- and staff-submitted listings (sell/rent/buy/lease/cooperation) flow
through Supabase (`listing_submissions` table) → `listing_ai_worker.py`
(local Ollama: classify, detect missing fields, clean up into a canonical
Chinese title/summary, keywords, alt text, dedupe hint) → staff review at
`/zh/admin/listing-desk/` → `listing_publisher.py` (reuses
`scripts/generate_site.py` to build real `/listings/{lang}/{slug}/` pages,
commits, pushes to `main` with the operator's own git credentials — no
token created). See `docs/listing-desk-v1.md` for setup and the daily cron.
