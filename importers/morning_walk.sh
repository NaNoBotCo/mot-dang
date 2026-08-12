#!/bin/zsh
# เดินเก็บตอนเช้า — the morning walk.
#
# Every morning the ants walk the same round: photograph the wichaa
# instruments, fetch today's weather and showtimes, re-harvest the event
# feeds, collect what people sent the worker overnight, then rebuild,
# verify, and publish. This is what makes the hero's "อัปเดตทุกวัน" true —
# and what keeps the cinema tile from ever again calling a Saturday sheet
# "today".
#
# Scheduled by ~/Library/LaunchAgents/net.motdang.morning-walk.plist
# (07:09 daily). Run it by hand any time: importers/morning_walk.sh
# Log: ~/Library/Logs/motdang-morning-walk.log
#
# Manners, in order:
#   - stands down (exit 0, says why) rather than racing another session:
#     dirty tree, diverged branch, or a build.py already running all mean
#     a person or another walk is mid-task and the morning can wait;
#   - every fetcher is allowed to fail alone — snapshot-first importers
#     keep what is on disk, so one dead feed never blocks the round;
#   - nothing is pushed unless the publish gate and route tests pass and
#     the docs/ tree is free of /Users/ paths, exactly the pre-push
#     sequence CLAUDE.md prescribes.

set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
REPO="${0:a:h:h}"   # importers/.. = repo root
LOG="$HOME/Library/Logs/motdang-morning-walk.log"
exec >>"$LOG" 2>&1
cd "$REPO" || exit 1

say() { print -- "$(date '+%F %T')  $*" }
stand_down() { say "ยืนดูเฉย ๆ วันนี้ — $1"; exit 0 }

say "== เดินเก็บตอนเช้า begins"

# one walk at a time
LOCK=/tmp/motdang-morning-walk.lock
if ! mkdir "$LOCK" 2>/dev/null; then stand_down "another walk holds the lock"; fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

# one build at a time (CLAUDE.md rule) — precise match, no self-match
if ps -eo args | grep -E '^python3? .*build\.py' >/dev/null; then
  stand_down "a build.py is already running"
fi

# a dirty tree means a person (or another session) is mid-task
if ! git diff --quiet || ! git diff --cached --quiet; then
  stand_down "the tree has uncommitted work"
fi

git fetch origin --quiet || stand_down "cannot reach origin"
LOCAL=$(git rev-parse main) REMOTE=$(git rev-parse origin/main)
if [[ "$LOCAL" != "$REMOTE" ]]; then
  git merge-base --is-ancestor main origin/main \
    && git pull --ff-only --quiet \
    || stand_down "main and origin/main have diverged"
fi

# --- the round: each stop may fail alone --------------------------------
python3 importers/make_widget_shots.py || say "widget shots kept yesterday's frames"
python3 importers/make_weather.py      || say "weather kept the snapshot"
python3 importers/make_air.py          || say "air quality kept the snapshot"
python3 importers/make_showtimes.py    || say "showtimes kept the snapshot"
python3 importers/harvest_events.py --refetch || say "events kept the snapshot"
python3 importers/sync_claims.py       || say "claims sync kept what is on disk"
python3 importers/sync_toilets.py      || say "toilet sync kept what is on disk"

# nothing new gathered -> nothing to say today
if git diff --quiet; then stand_down "no fresh data — the town is as it was"; fi

# today's date onto every footer
TODAY=$(date +%F)
sed -i '' -E "s/^BUILD_DATE = \"[0-9-]+\"/BUILD_DATE = \"$TODAY\"/" build.py

python3 build.py || { say "BUILD FAILED — nothing pushed"; exit 1 }

# the pre-push sequence, same as by hand
python3 tests/test_publish_gate.py || { say "publish gate FAILED — nothing pushed"; exit 1 }
node tests/test_plan_routes.js     || { say "route tests FAILED — nothing pushed"; exit 1 }
if grep -rl "/Users/" docs/ | head -1 | grep -q .; then
  say "path leak in docs/ — nothing pushed"; exit 1
fi
[[ -f docs/CNAME ]] || { say "docs/CNAME missing — nothing pushed"; exit 1 }

git add -A
git commit --quiet -m "Morning walk — $TODAY" \
  --author="NaNoBotCo <skunkhaus@gmail.com>" || stand_down "nothing to commit"
git push --quiet origin main || { say "PUSH FAILED — commit kept locally"; exit 1 }
python3 importers/ping_indexnow.py || say "IndexNow ping skipped"
say "== published $TODAY — the ants are home"
