# Listing Desk v1 — setup & runbook

Structured, AI-assisted, staff-reviewed listing submissions for VietnamZiChan.
Reuses the existing shared Supabase auth/community project and the existing
static site generator (`scripts/generate_site.py`) instead of building a new
publish path from scratch.

## Pipeline

```
user or staff fills in /zh|vi|en/submit/
        │  (RLS: only the submitter can see their own RAW row)
        ▼
listing_submissions.status = RAW
        │  automation/listing_ai_worker.py  (local Ollama, cron 10:00 & 17:00)
        ▼
status = AI_PROCESSED  →  PENDING_REVIEW  (or NEEDS_INFO if a required field is missing)
        │  staff reviews at /zh/admin/listing-desk/  (Approve / Reject / Needs info)
        ▼
status = APPROVED
        │  automation/listing_publisher.py  (same cron run, right after the worker)
        │  → appends to data/listings.json
        │  → runs scripts/generate_site.py (existing generator) for zh/vi/en
        │  → runs scripts/health_check.py
        │  → git commit + git push to main  (your own git credentials — no token created)
        │  → Cloudflare Pages auto-deploys main
        ▼
status = PUBLISHED, published_url = https://vietnamzichan.com/listings/{lang}/{slug}/
```

## One-time setup (on your Mac, next to Ollama)

1. `cp automation/.env.example automation/.env` and fill in:
   - `SUPABASE_SERVICE_ROLE_KEY` — Supabase dashboard → this project → Settings →
     API → `service_role` secret. **Never commit this file** (already in
     `.gitignore`). This key bypasses Row Level Security, so it must only ever
     live in `automation/.env` on your own machine.
   - `OLLAMA_MODEL` — whatever model you actually have pulled
     (`ollama list`). The default `qwen2.5:7b-instruct` is a placeholder.
2. Make sure `git push` works from this machine without any prompt (your own
   SSH key or credential helper already authenticated against
   `yuguanbo020-svg/vietnamzichan-site`, `main` branch). The publisher script
   does not create a GitHub token and does not touch repo permissions — it
   just runs `git push` as you.
3. `chmod +x automation/listing_desk_cron.sh`
4. Add to `crontab -e` (adjust the path):
   ```
   0 10 * * * /usr/bin/env bash /path/to/vietnamzichan-site/automation/listing_desk_cron.sh >> /path/to/vietnamzichan-site/automation/logs/cron.log 2>&1
   0 17 * * * /usr/bin/env bash /path/to/vietnamzichan-site/automation/listing_desk_cron.sh >> /path/to/vietnamzichan-site/automation/logs/cron.log 2>&1
   ```
   (macOS: `cron` needs Full Disk Access under System Settings → Privacy, or
   use `launchd` instead if you prefer — same two commands either way.)

## Database (already applied for real)

`docs/supabase/010_listing_desk_v1.sql` — applied directly via the Supabase
SQL Editor on 2026-09-07 against the live shared project
(`rpfccljejzfixohgwtpr`). Creates `listing_submissions`, `site_staff`, the
`is_site_staff()` helper, RLS policies, and the `listing-images` public
storage bucket. All statements are idempotent, so it's safe to re-run if you
ever need to reapply it (e.g. against a fresh project).

Your existing admin account (the same UID already used for the cross-site
`posts` admin policies) was inserted into `site_staff` for
`site='vietnamzichan'`, so you can use `/zh/admin/listing-desk/` immediately.
To add another staff member later, run (in the SQL Editor):
```sql
insert into public.site_staff (user_id, site, role)
values ('<their auth.users.id>', 'vietnamzichan', 'staff');
```
There is no self-service "become staff" button by design — this is an
intentionally manual, low-frequency action.

## Manual dry run (recommended before trusting cron)

```bash
cd vietnamzichan-site
python3 automation/listing_ai_worker.py     # RAW -> PENDING_REVIEW / NEEDS_INFO
# … approve at least one item at /zh/admin/listing-desk/ …
GIT_PUSH=0 python3 automation/listing_publisher.py   # commits locally, does NOT push
git show --stat HEAD                        # inspect the commit before trusting it
python3 automation/listing_publisher.py     # (if it looks right) run again with GIT_PUSH=1, or just push manually
```

## What is NOT wired up yet (known gaps, honest list)

- No image compression/resizing on upload (`js/listing-desk.js` just caps file
  size at 8MB per image and pushes to Supabase Storage as-is).
- `listing_publisher.py` publishes a listing page but does not yet delete the
  Supabase row's images from storage on REJECTED (they're small, private-ish,
  not indexed — low priority cleanup).
- The generated listing pages use `scripts/generate_site.py`'s existing plain
  template (no site.css nav/footer chrome), matching what that generator
  already produces for aggregated feed items elsewhere on the site — visual
  parity with the hand-built category/city pages is a follow-up, not a
  Phase-1 blocker.
- `automation/listing_ai_worker.py` and `ollama_translate.py` assume a model
  that reliably returns JSON when asked (`format: "json"` in the Ollama
  request). If your pulled model ignores that, tighten the prompt or switch
  models — the scripts log the raw failure to `automation/logs/`.
- Dedupe is currently just a hint string from the model (`ai.dedupe_hint`),
  shown to staff during review — there's no automatic duplicate rejection
  yet.
