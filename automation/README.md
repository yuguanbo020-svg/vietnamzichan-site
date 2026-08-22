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
