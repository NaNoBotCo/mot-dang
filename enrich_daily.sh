#!/bin/bash
# The demand loop. Everything here is idempotent.
#
#   ./enrich_daily.sh              the whole loop
#   ./enrich_daily.sh --no-gpt     skip the archive pass (it is the slow one)
#
# Runs by hand, not on a schedule: step 1 embeds through Workers AI at
# api.cloudflare.com and step 3 sends up to 300 queries to the live index,
# both metered. Step 7 (box_misses.py) also runs daily at 08:20 from
# importers/pull_inbox.sh; it stays here so one run is still the whole loop.
set -euo pipefail
cd "$(dirname "$0")"
WLAI="$HOME/Developer/claude code projects/white-label-ai"

echo "== 1. is the assistant's index still level with the corpus?"
python3 "$WLAI/scripts/index_motdang.py" --check || {
  echo "   → behind; catching it up"
  python3 "$WLAI/scripts/index_motdang.py"
}

echo "== 2. harvest the demand"
if [ "${1:-}" = "--no-gpt" ]; then
  python3 enrich.py harvest --source ai
  python3 enrich.py harvest --source asked
else
  python3 enrich.py harvest
fi

echo "== 3. put the open questions to the live index"
python3 enrich.py score --limit 300

echo "== 4. why each one failed, with evidence from this disk"
python3 enrich.py classify

echo "== 5. the queue and the build file"
python3 enrich.py report

echo "== 6. the assistant's own gap harvest, into this repo"
python3 "$WLAI/scripts/gaps.py" --mark || true
python3 "$WLAI/scripts/asked_drafts.py" || true

echo "== 7. what the search box could not answer (WO-84, 2026-09-10)"
python3 importers/box_misses.py --days 14 > /dev/null && echo "   → _incoming/box-misses-$(date +%F).txt" || true

echo
echo "Read: _incoming/enrich/queue-$(date +%F).txt"
