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

# one walk at a time — SHARED WITH standing_walk.sh, which does the publishing
# half of this same job every twenty minutes. The two must never be halfway
# through each other: this walk rewrites data/ while that one would be reading
# it to build. Same lock, so whoever arrives second waits for the next round.
#
# WAIT FOR IT, DO NOT GIVE UP ON IT. This used to stand down the moment the
# lock was taken, and a standing-walk round (every twenty minutes, a build
# plus a publish inside) is nearly always holding it at 07:09. From 2026-09-13
# to 2026-09-25 the morning walk stood down every single day, and nothing else
# fetches finance, showtimes, lottery, events or festival dates: the site went
# on printing a 10 September exchange rate. There is no next round for this
# walk for twenty-four hours, so it waits for the standing round to finish.
LOCK=/tmp/motdang-walk.lock
# A lock records its holder. One whose process is gone (a walk killed
# mid-round cannot run its trap) is announced and taken, as build.py treats
# cache/build.lock; before this, one SIGKILL would have stood both walks down
# for good. A pid-less lock is from before that and counts as stale at 3 h.
walk_lock_stale() {
  local holder
  holder=$(cat "$LOCK/pid" 2>/dev/null)
  if [[ -n "$holder" ]]; then ! kill -0 "$holder" 2>/dev/null; return; fi
  [[ -n $(find "$LOCK" -maxdepth 0 -mmin +180 2>/dev/null) ]]
}
take_walk_lock() {
  mkdir "$LOCK" 2>/dev/null && { print $$ > "$LOCK/pid"; return 0 }
  if walk_lock_stale; then
    say "the walk lock's holder ($(cat "$LOCK/pid" 2>/dev/null || print unknown)) is gone — taking it"
    rm -rf "$LOCK"
    mkdir "$LOCK" 2>/dev/null && { print $$ > "$LOCK/pid"; return 0 }
  fi
  return 1
}
WAITED=0
until take_walk_lock; do
  (( WAITED == 0 )) && say "another walk holds the lock — waiting for it"
  (( WAITED >= 150 )) && stand_down "another walk held the lock for 150 minutes"
  sleep 60; (( WAITED++ ))
done
(( WAITED > 0 )) && say "lock free after ${WAITED} min"
trap 'rm -rf "$LOCK" 2>/dev/null' EXIT

# one build at a time (CLAUDE.md rule)
#
# ASK THE LOCK, NOT ps. This used to match `^python3? .*build\.py`, and ps
# prints the resolved interpreter — `/Library/.../MacOS/Python build.py` — so
# that anchor could never match and the check passed every morning without
# looking at anything. build.take_build_lock() writes the holder's pid to
# cache/build.lock and is the mechanism the project actually trusts; a lock
# whose process is gone is stale by that function's own rule and ignored here
# exactly as build.py would ignore it.
# Same patience as the walk lock: a build holding it will finish.
BWAIT=0
while [[ -f cache/build.lock ]]; do
  HOLDER=$(head -1 cache/build.lock 2>/dev/null | tr -d '[:space:]')
  [[ -n "$HOLDER" ]] && kill -0 "$HOLDER" 2>/dev/null || break
  (( BWAIT == 0 )) && say "cache/build.lock is held by live pid $HOLDER — waiting for it"
  (( BWAIT >= 150 )) && stand_down "cache/build.lock held by live pid $HOLDER for 150 minutes"
  sleep 60; (( BWAIT++ ))
done
# Anchored at the END, because a shell wrapper whose command line merely
# CONTAINS the words "build.py" is a session that ran a build, not a build.
if ps -eo args | grep -E '[b]uild\.py$' >/dev/null; then
  stand_down "a build.py is already running"
fi

# Whose edits are in flight? The walk owns its own output — data snapshots,
# the built docs/ tree, regenerated assets, and build.py's BUILD_DATE line.
# Anything ELSE dirty means a person is mid-task in the source. The old rule
# stood the whole walk down for that, and the log then read "ยืนดูเฉย ๆ" eight
# mornings running while the town's weather froze; the town was never the
# thing that was busy. Now a busy source only postpones the BUILD — the
# gathering half always walks, so the next build (whoever runs it) ships
# this morning's numbers, not last week's.
PUBLISH_HOLD=""
DIRTY_SOURCE=$(git status --porcelain -- . \
  ':(exclude)data' ':(exclude)docs' ':(exclude)assets' ':(exclude)cache' \
  ':(exclude).github' \
  | grep -v '^.. build\.py$' || true)
DIRTY_BUILDPY=$(git status --porcelain -- build.py || true)
[[ -n "$DIRTY_SOURCE$DIRTY_BUILDPY" ]] && PUBLISH_HOLD="source files are mid-task"

# No fetch, no pull, no divergence check. There is one copy of this history and
# it is on this machine; there is nothing to diverge FROM. Leaving the old
# check in would have been a slow trap: it set PUBLISH_HOLD when it could not
# reach origin, so the day GitHub stops answering for good, the walk would
# stand down every morning and quietly publish nothing — while every fetcher
# above went on succeeding.

# --- the round: each stop may fail alone --------------------------------
python3 importers/make_widget_shots.py || say "widget shots kept yesterday's frames"
python3 importers/make_weather.py      || say "weather kept the snapshot"
python3 importers/make_air.py          || say "air quality kept the snapshot"
python3 importers/harvest_firms.py     || say "fire hotspots kept the snapshot"
python3 importers/make_ping.py         || say "river gauges kept the snapshot"
python3 importers/make_showtimes.py    || say "showtimes kept the snapshot"
python3 importers/make_lottery.py      || say "lottery kept the snapshot"
python3 importers/make_finance.py      || say "finance kept the snapshot"
python3 importers/sites_traffic.py     || say "site visits kept the last count"
python3 importers/make_horo.py         || say "horoscope kept the previous bake"
python3 importers/make_shuffle.py      || say "scripture shuffle kept the previous bake"
python3 importers/pull_events_mail.py || say "events@ mail: the ear did not answer"
python3 importers/fetch_newsletter.py  || say "Steve's newsletter: the last issue stands"
python3 importers/harvest_events.py --refetch || say "events kept the snapshot"
# Each event's link down the ladder: its source's, its series' kept one, its venue's site; each checked.
python3 importers/event_links.py       || say "event links kept the last run"
# Mondays, the week's issue (publish/newsletter.js sends it; test address only until NEWSLETTER_LIVE).
[[ $(date +%u) == 1 ]] && { python3 importers/make_newsletter.py --send --quiet || say "the weekly issue was not sent"; }
# Festival dates were gathered once, on 2026-07-29, and then never again — the
# walk collected events every morning and walked straight past the festivals.
# A canon of 33 with no way to get a date is a calendar that cannot tell you
# when anything is. It rides along now; STALE_DAYS keeps it from refetching
# more often than announcements actually change.
python3 importers/harvest_festivals.py || say "festival dates kept the snapshot"
[[ $(date +%u) == 1 ]] && { python3 importers/harvest_inat.py || say "iNaturalist kept last week's sightings"; }
# Link health. The publish gate refuses a build that links a URL
# check_links.py found dead, and data/linkhealth.json is its only evidence —
# written 2026-08-21 and never since, because nothing ran the checker.
# Snapshot-first: a verdict under STALE_DAYS is reused, so most mornings this
# costs seconds. The bounds cover the rest: 2026-09-11, the first morning it
# ran, every verdict had aged out at once and the unbounded checker held the
# walk for over four hours — two checking 13,170 links, the rest in one-at-a-
# time archive lookups. 800 checks a morning turns the whole set over in
# under three weeks, inside the 30-day life; 150 lookups is about ten minutes.
python3 importers/check_links.py --max 800 --wayback-max 150 || say "link health kept the last check"
python3 importers/sync_claims.py       || say "claims sync kept what is on disk"
python3 importers/sync_toilets.py      || say "toilet sync kept what is on disk"
# What readers told the ants overnight. It lands in _incoming/ (gitignored —
# a suggestion carries the sender's own email so we can ask them a question,
# and that must never ride into a public commit). Nothing here reaches the
# site on its own; somebody reads it.
python3 importers/sync_suggestions.py  || say "suggestion queue not read this morning"

# Count what came home, not just who came home. Every fetcher above can fail
# by writing today's date over an empty basket and exiting 0 — which is how the
# site came to publish an events page with no events and a cinema widget with
# no cinemas, refreshed faithfully every morning, for weeks. This does not stop
# the walk: yesterday's good data is better than no site, and a bad basket is a
# thing to be told about, not to halt for.
python3 importers/watch_data.py || say "⚠️  a source came home empty — see the list above"

# nothing new gathered -> nothing to say today (fetchers write only data/ + assets/)
if git diff --quiet -- data assets; then stand_down "no fresh data — the town is as it was"; fi

# a busy source postpones the build, never the gathering
if [[ -n "$PUBLISH_HOLD" ]]; then
  stand_down "ข้อมูลสดเก็บแล้ว รอสร้างรอบหน้า — $PUBLISH_HOLD; fresh data is on disk for the next build"
fi

# today's date onto every footer
# Building on motdang-build (cache/build-on-server): the morning's data is
# gathered; the standing walk's next round hands it to the server.
if [[ -f cache/build-on-server ]]; then
  stand_down "fresh data is on disk; the standing walk hands it to the server"
fi
TODAY=$(date +%F)
sed -i '' -E "s/^BUILD_DATE = \"[0-9-]+\"/BUILD_DATE = \"$TODAY\"/" build.py

# Shelf and question cards first — signature-based, so only what changed is
# drawn. Soft: it needs Chrome, and a missing card falls back to the brand.
python3 make_shelf_cards.py || say "shelf cards kept — missing ones fall back to the brand card"
python3 build.py || { say "BUILD FAILED — nothing pushed"; exit 1 }

# the pre-push sequence, same as by hand
python3 tests/test_publish_gate.py || { say "publish gate FAILED — nothing pushed"; exit 1 }
node tests/test_plan_routes.js     || { say "route tests FAILED — nothing pushed"; exit 1 }
# The 404 page's side-scroller. Hard, for one of its checks only: the game
# must not take a keystroke from the search box, which is the whole job of
# the page it sits on. Needs no build — it reads assets/soi_run.js.
node tests/test_soi_run.js         || { say "soi_run FAILED — nothing pushed"; exit 1 }
# A published reader question must have its records, its page, its card and
# a reply that fills. Hard: a broken one is a wrong answer with the site's
# name on it. A half-answered question carries draft:true and is skipped.
python3 tests/test_asked.py         || { say "asked gate FAILED — nothing pushed"; exit 1 }
# Advisory: its NO CARD mode fires legitimately when Chrome was away.
python3 tests/test_shelf_cards.py   || say "⚠️  shelf cards advisory — some list pages share as the brand card"
if grep -rl "/Users/" docs/ | head -1 | grep -q .; then
  say "path leak in docs/ — nothing pushed"; exit 1
fi
# Only what the walk itself gathered and built — never a sweep of the whole
# tree, so a session's half-finished work can never ride out in this commit.
git add -A -- build.py data docs assets
git commit --quiet -m "Morning walk — $TODAY" \
  --author="NaNoBotCo <skunkhaus@gmail.com>" || stand_down "nothing to commit"
# The walk commits but does not push. Nothing in the serving path needs it —
# the site goes out through R2 — so the walk keeps its job small and leaves the
# remote to a deliberate hand. The archive below is the copy that leaves this
# machine. To have the walk push as well, add `"$HOME/.claude/bin/pr-push" .` here; it
# must stay best-effort so a remote hiccup can never fail a morning that
# already gathered, built and committed.
# Weekly, not daily: mot-dang alone bundles to ~600 MB because docs/ is
# committed, so the history carries every built page. Sunday, whole fleet,
# last three per repo.
#
# It writes to the nanobotco-backup bucket and MUST NOT be pointed at
# mot-dang-site: deploy.py syncs docs/ onto that bucket, and rclone sync
# deletes whatever is in the destination and not in the source. The first
# version of this uploaded into mot-dang-site/backup/, reported success, and
# was erased by the deploy a few minutes later.
if [[ $(date +%u) == 7 ]]; then
  python3 importers/offsite_backup.py --all || say "offsite backup FAILED — history is only on this machine"
fi
# WHAT READERS SEE: motdang.net is the mot-dang-site Worker over R2
# (publish/README.md). The R2 sync IS the deploy.
# Through the tower, on the cloudflare-deploy lane, so a morning publish can
# never land on top of the wichaa nightly, the crawler's publish step, or a
# standing_walk.sh round. Waits rather than stepping back: unlike the standing
# walk there is no next round for twenty-four hours, so patience is the right
# manner here.
python3 "/Users/annikapeacock/Developer/claude code projects/bot-tower/tower.py" \
  wrap cloudflare-deploy --patience 20 -- python3 publish/deploy.py --yes \
  || say "R2 site sync FAILED — readers still see yesterday"
python3 importers/ping_indexnow.py || say "IndexNow ping skipped"
say "== published $TODAY — the ants are home"
