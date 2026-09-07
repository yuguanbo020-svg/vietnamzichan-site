#!/usr/bin/env bash
# Listing Desk v1 — daily batch chain. Meant to run on the Owner's own Mac via cron/launchd,
# NOT in CI and NOT on any cloud AI session. Needs automation/.env filled in locally
# (see automation/.env.example) and a local Ollama server running.
#
# Suggested crontab (crontab -e), Vietnam-facing site but times below are your machine's
# local time — adjust if you want them anchored to Asia/Ho_Chi_Minh specifically:
#   0 10 * * * /usr/bin/env bash /path/to/vietnamzichan-site/automation/listing_desk_cron.sh >> /path/to/vietnamzichan-site/automation/logs/cron.log 2>&1
#   0 17 * * * /usr/bin/env bash /path/to/vietnamzichan-site/automation/listing_desk_cron.sh >> /path/to/vietnamzichan-site/automation/logs/cron.log 2>&1
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "== $(date -u +%FT%TZ) listing_desk_cron start =="

python3 automation/listing_ai_worker.py || echo "listing_ai_worker exited non-zero (see log, continuing to publisher)"
python3 automation/listing_publisher.py

echo "== $(date -u +%FT%TZ) listing_desk_cron done =="
