#!/bin/zsh
# เดินเก็บเรื่อย ๆ — the standing walk.
#
# The ants do not wait to be told. This goes round every twenty minutes,
# forever, and publishes whatever the maker bots have finished. Nobody asks
# whether to publish; that question has an answer and this file is it.
#
# HOW IT DIVIDES WITH THE MORNING WALK. morning_walk.sh (07:09) is the GATHER:
# the daily fetchers with a cadence of their own — showtimes, lottery, finance,
# events, festivals — and it writes them to disk whether or not it goes on to
# build. This is the PUBLISH: it picks up whatever is on disk, from that gather
# or from any session's work, and puts it in front of readers. The two compose
# without either knowing about the other, which is why the morning walk needed
# no rewriting when this arrived; they share a lock so they can never be
# halfway through each other.
#
# WHY QUIET AND NOT CLEAN. The morning walk stands down from BUILDING when any
# source file is dirty. That reads as caution and is really a stall: the tree
# is nearly always dirty, because a session is nearly always mid-order, and the
# log shows it published 2 mornings out of 14 while three weeks of finished
# shelves sat unpublished. So this asks a different question — has anyone
# TOUCHED the source in the last QUIET_MINUTES? A tree nobody has written to
# for ten minutes is a tree between edits, not a tree mid-edit. The hard gates
# further down are what actually keep a broken build off the site.
#
# WHY A CHANGE GATE. Rebuilding is not free: build.py rewrites ~36,000 files,
# and the first evening of this walk republished a byte-identical site four
# times in ninety minutes because the weather had been refetched at the top of
# each round. So the weather now comes AFTER the decision to build rather than
# causing it, and the decision belongs to importers/walk_fingerprint.py —
# which knows two things this file should not have to: mtimes are not news
# (the inbox syncs rewrite their files every round), and neither are the
# `generated` stamps the writers put INSIDE their output (data/claims.json
# carries the moment the worker answered, and hashing that raw made round two
# rebuild the whole site to ship a timestamp). Its `diff` names what actually
# changed, so the log reads as a reason and not a verdict.
#
# Resting:  cache/walk-rest — if that file exists the walk stands down. Empty
#           means rest until you remove it; an ISO timestamp inside means rest
#           until then, and the walk clears it itself when the time passes.
#           Every shape isoformat() writes is honored — bare local, ...Z,
#           ±HH:MM — and a date the check cannot read or compare rests like
#           an empty file does: only a proven expiry ever removes the rest,
#           because the file may be another session's and is not ours to lose.
#           NOTHING ELSE STOPS IT. There is no window and no arming step: the
#           default is that finished work reaches readers.
# Gate:     importers/walk_fingerprint.py vs cache/last-published.json —
#           what a build reads, hashed with the volatile stamps dropped.
# Ledger:   cache/standing-walk.jsonl — one line per round, what it did and why.
# Log:      ~/Library/Logs/motdang-standing-walk.log (rotated at 5 MB)
# Plist:    ~/Library/LaunchAgents/net.motdang.standing-walk.plist (every 20 min)
#
# It does NOT commit. The morning walk commits because it owns everything it
# touched; here the source belongs to whichever session is editing it, and a
# commit mixing their half-done work with built output would be a confusing
# thing to find in the history. What shipped is in the ledger.

set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
REPO="${0:a:h:h}"   # importers/.. = repo root
LOG="$HOME/Library/Logs/motdang-standing-walk.log"

# A perpetual job needs somewhere for its log to go. Rotate before the first
# line, so a round is never split across two files.
if [[ -f "$LOG" ]] && (( $(stat -f %z "$LOG" 2>/dev/null || echo 0) > 5242880 )); then
  mv -f "$LOG" "$LOG.1" 2>/dev/null
fi
exec >>"$LOG" 2>&1
cd "$REPO" || exit 1

REST="cache/walk-rest"
LEDGER="cache/standing-walk.jsonl"
STAMP="cache/last-published.json"
TOWER="/Users/annikapeacock/Developer/claude code projects/bot-tower/tower.py"
QUIET_MINUTES=${MD_QUIET_MINUTES:-10}
MAX_AGE_HOURS=${MD_MAX_AGE_HOURS:-20}

say() { print -- "$(date '+%F %T')  $*" }

note() {   # note <verdict> <detail>   — one line in the ledger, for reading later
  python3 - "$1" "$2" <<'PY' >>"$LEDGER" 2>/dev/null
import json, sys, time
print(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                  "verdict": sys.argv[1], "detail": sys.argv[2]},
                 ensure_ascii=False))
PY
}

stand_down() { say "ยืนดูเฉย ๆ รอบนี้ — $1"; note "stood-down" "$1"; exit 0 }

say "== เดินเก็บเรื่อย ๆ begins"

# --- is the walk resting? ------------------------------------------------
# Read first, before anything can cost time or touch the network. An empty
# file rests until somebody removes it; a timestamp rests until that moment
# and then clears itself, so a rest can be set and forgotten.
#
# Sessions write this timestamp in whatever shape isoformat() handed them —
# bare local, ...Z, +00:00, +07:00 — so both sides are normalized to aware
# UTC before comparing (fromisoformat before 3.11 cannot read a trailing Z,
# and an offset date once made the old naive-now() comparison throw; the
# traceback fell through to the rm below and deleted a live rest). The check
# exits 0 ONLY on a proven expiry: parse errors, comparison errors, even a
# missing python3 all land in the else and KEEP the file. Failing toward
# walking destroys other sessions' rests; failing toward resting costs
# twenty minutes.
if [[ -f "$REST" ]]; then
  UNTIL=$(head -1 "$REST" 2>/dev/null | tr -d '[:space:]')
  if [[ -z "$UNTIL" ]]; then
    stand_down "resting — $REST is set (remove it to walk again)"
  fi
  if python3 -c "
import sys, datetime
def expired(raw):
    s = raw.strip()
    if s[-1:] in ('Z', 'z'):
        s = s[:-1] + '+00:00'
    until = datetime.datetime.fromisoformat(s)
    if until.tzinfo is None:
        until = until.astimezone()   # a bare wall time means local time
    return datetime.datetime.now(datetime.timezone.utc) >= until
try:
    sys.exit(0 if expired(sys.argv[1]) else 1)
except Exception:
    sys.exit(1)   # unreadable or uncomparable — an open-ended rest, never an expired one
" "$UNTIL"; then
    rm -f "$REST"
    say "rest ended $UNTIL — walking again"
  else
    stand_down "resting until $UNTIL"
  fi
fi

# --- one walk at a time --------------------------------------------------
# SHARED WITH THE MORNING WALK on purpose. They do different halves of the
# same job and must never be halfway through each other: the gather rewrites
# data/ while a build would be reading it.
LOCK=/tmp/motdang-walk.lock
if ! mkdir "$LOCK" 2>/dev/null; then stand_down "another walk holds the lock"; fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# --- one build at a time (CLAUDE.md rule) --------------------------------
# ASK THE LOCK, NOT ps. build.take_build_lock() writes the holder's pid to
# cache/build.lock and is the mechanism the project actually trusts. A lock
# whose process is gone is stale by that function's own rule, so it is ignored
# here exactly as build.py would ignore it.
if [[ -f cache/build.lock ]]; then
  HOLDER=$(head -1 cache/build.lock 2>/dev/null | tr -d '[:space:]')
  if [[ -n "$HOLDER" ]] && kill -0 "$HOLDER" 2>/dev/null; then
    stand_down "cache/build.lock is held by live pid $HOLDER"
  fi
fi
# Anchored at the END, because a shell wrapper whose command line merely
# CONTAINS the words "build.py" is a session that ran a build, not a build.
if ps -eo args | grep -E '[b]uild\.py$' >/dev/null; then
  stand_down "a build.py is already running"
fi

# --- has the source stopped moving? --------------------------------------
# data/, docs/, assets/ and cache/ are what the walks themselves write, so they
# are never evidence of somebody else working. Everything else is source.
BUSY=$(python3 - "$QUIET_MINUTES" <<'PY'
import os, sys, time
cutoff = time.time() - int(sys.argv[1]) * 60
skip = {".git", "docs", "cache", "data", "assets", "_incoming",
        "node_modules", ".venv", "__pycache__"}
newest, name = 0.0, ""
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
    for f in files:
        if f.startswith("."):
            continue
        p = os.path.join(root, f)
        try:
            m = os.path.getmtime(p)
        except OSError:
            continue
        if m > newest:
            newest, name = m, p
if newest > cutoff:
    print("%s (%.0f min ago)" % (name.lstrip("./"), (time.time() - newest) / 60))
PY
)
[[ -n "$BUSY" ]] && stand_down "source still moving — $BUSY"

# --- what came in while we were away -------------------------------------
# Cheap, keyless, our own worker. These run BEFORE the change gate because a
# claim or a toilet report is exactly the kind of news worth a rebuild.
python3 importers/sync_claims.py      || say "claims sync kept what is on disk"
python3 importers/sync_toilets.py     || say "toilet sync kept what is on disk"
python3 importers/sync_suggestions.py || say "suggestion queue not read this round"

# --- fold in finished crawls ---------------------------------------------
# import_all.py reads cache/overpass/ wholesale and rewrites data/canonical/.
# A crawl still writing into that cache can hand it a half-written file, and a
# truncated group imports as an empty one — the same failure CLAUDE.md warns
# about for Overpass remarks, arriving by a different door. So the import waits
# for the crawler to come home, and the build ships what is already imported
# meanwhile. The next round catches the new shelf.
if ps -eo args | grep -E '[c]rawl_overpass\.py' >/dev/null; then
  say "a crawl is still out — importing nothing this round, building what is already home"
else
  python3 importers/import_all.py       || { say "import FAILED — nothing published"; note "failed" "import_all"; exit 1 }
  python3 importers/build_streets.py    || say "streets kept the last pass"
  python3 importers/build_open_lamps.py || say "lamp schedules kept the last pass"
fi

# --- is there anything new to say? ---------------------------------------
# walk_fingerprint.py compares what a build would read (source + data +
# assets, volatile stamps dropped) against what the last publish read, and
# prints one line per real difference. Empty means the town is as it was.
# A missing or unreadable store prints a line saying so, which correctly
# fails toward publishing.
CHANGES=$(python3 importers/walk_fingerprint.py diff "$STAMP")
if [[ -z "$CHANGES" ]]; then
  # Nothing has changed. Publish anyway if the site is about to date itself
  # older than a day — the footer says อัปเดตทุกวัน and that should be true
  # even through a quiet stretch.
  AGE_H=$(python3 -c "
import os, time, sys
print(int((time.time() - os.path.getmtime(sys.argv[1])) / 3600))" "$STAMP")
  if (( AGE_H < MAX_AGE_HOURS )); then
    stand_down "ไม่มีอะไรใหม่ — nothing has changed since the last publish (${AGE_H}h ago)"
  fi
  say "nothing new, but the last publish was ${AGE_H}h ago — walking anyway to keep the date true"
else
  N=$(print -- "$CHANGES" | grep -c .)
  say "what changed ($N):"
  print -- "$CHANGES" | head -10 | while read -r line; do say "    $line"; done
  (( N > 10 )) && say "    … and $((N - 10)) more"
fi

# --- now that we are building, make the numbers current ------------------
# AFTER the gate, never before: these change every single time they run, so
# running them first would make every round look like news and this walk would
# rebuild the whole site every twenty minutes forever.
python3 importers/make_weather.py || say "weather kept the snapshot"
python3 importers/make_air.py     || say "air quality kept the snapshot"
python3 importers/watch_data.py   || say "⚠️  a source came home empty — see the list above"

# today's date onto every footer
TODAY=$(date +%F)
sed -i '' -E "s/^BUILD_DATE = \"[0-9-]+\"/BUILD_DATE = \"$TODAY\"/" build.py

# Shelf and question cards. Signature-based: it redraws only the ones whose
# picture would differ, so this is seconds on a quiet day. Soft-fails —
# it needs Chrome, and a missing card falls back to the brand card by
# design, which is a worse share but never a broken page.
python3 make_shelf_cards.py || say "shelf cards kept — missing ones fall back to the brand card"
python3 build.py || { say "BUILD FAILED — nothing published"; note "failed" "build.py"; exit 1 }

# --- the pre-publish sequence, same as by hand ---------------------------
python3 tests/test_publish_gate.py || { say "publish gate FAILED — nothing published"; note "failed" "publish gate"; exit 1 }
# A published reader question must have its records, its page, its card and
# a reply that fills. Hard, because a broken one is a wrong answer with the
# site's name on it — a half-answered question carries draft:true in
# data/asked.json and is skipped, which is the valve.
python3 tests/test_asked.py || { say "asked gate FAILED — nothing published"; note "failed" "asked gate"; exit 1 }
# Advisory: its NO CARD mode fires legitimately when Chrome was away.
python3 tests/test_shelf_cards.py || say "⚠️  shelf cards advisory — some list pages share as the brand card"
# Advisory: the 🏷 tag layer's counts, thresholds and pills (tests/test_tags.py).
# A drift here is a wrong count on a tag page, not a broken site — say so, ship.
python3 tests/test_tags.py >/dev/null 2>&1 || say "⚠️  tags advisory — tests/test_tags.py failed; tag pages may disagree with places.json"
# Advisory: a borrowed pin must never claim to be surer than the record it
# was copied from (tests/test_pins.py). A wrong error bar is a quiet wrong
# answer, not a broken page — say it, ship it.
python3 tests/test_pins.py >/dev/null 2>&1 || say "⚠️  pins advisory — a borrowed pin claims more precision than its source"
node tests/test_plan_routes.js     || { say "route tests FAILED — nothing published"; note "failed" "route tests"; exit 1 }
if grep -rl "/Users/" docs/ | head -1 | grep -q .; then
  say "path leak in docs/ — nothing published"; note "failed" "path leak in docs/"; exit 1
fi
[[ -f docs/CNAME ]] || { say "docs/CNAME missing — nothing published"; note "failed" "no CNAME"; exit 1 }

# deploy.py has its own floor, but failing here costs a second instead of a
# full bucket listing, and says the number out loud in the log.
COUNT=$(python3 -c "
import pathlib
print(sum(1 for p in pathlib.Path('docs').rglob('*') if p.is_file()))")
say "docs/ holds $COUNT files"
if (( COUNT < 20000 )); then
  say "REFUSING — $COUNT files is a broken build, not a small site"
  note "failed" "docs floor: $COUNT files"; exit 1
fi

# --- publish -------------------------------------------------------------
# Through the tower, on the cloudflare-deploy lane, so this can never land on
# top of the wichaa nightly or the crawler's own publish step. --no-wait
# because there is another tick in twenty minutes and waiting would only make
# two walks queue up behind each other.
python3 "$TOWER" wrap cloudflare-deploy --no-wait -- python3 publish/deploy.py --yes
RC=$?
if (( RC == 75 )); then
  stand_down "the cloudflare-deploy lane was busy; the next round will take it"
elif (( RC != 0 )); then
  say "R2 site sync FAILED ($RC) — readers still see the last good build"
  note "failed" "deploy.py exit $RC"; exit 1
fi

python3 importers/ping_indexnow.py || say "IndexNow ping skipped"

# --- remember what we just published -------------------------------------
# Recorded here, AFTER weather/air/BUILD_DATE, not before: those changed
# after the diff above was taken, and storing the BEFORE state would make the
# next round see this round's own work as somebody's news and rebuild every
# twenty minutes — the exact loop the gate exists to break.
python3 importers/walk_fingerprint.py write "$STAMP" \
  || say "⚠️  could not record the fingerprint — next round will rebuild once"

say "== published $TODAY $(date '+%H:%M') — $COUNT files, the ants are home"
note "published" "$COUNT files; $(print -- "${CHANGES:-first publish}" | head -1)"
