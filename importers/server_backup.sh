#!/bin/bash
# server_backup.sh — a dated copy of the source on the Storage Box, nightly.
#
# /srv/mot-dang.in is the laptop's tree as the walk last sent it, .git included,
# and every hand-off mirrors it with rsync --delete: a tree wiped on the laptop
# (2026-10-08) is wiped here one round later. This keeps 14 nights of it on the
# Storage Box (u682729, motdang/src/<date>/), each night hard-linked to the one
# before, so only changed files take space. /srv/state goes beside it.
#
# Run by motdang-backup.timer as root (root holds the Storage Box key).
#   restore one file:  rsync -e 'ssh -p 23' u682729@u682729.your-storagebox.de:motdang/src/<date>/<path> .
set -u
BOX=u682729@u682729.your-storagebox.de
SSH="ssh -p 23 -o BatchMode=yes -o ConnectTimeout=30"
STAGE=/srv/mot-dang.in
FREEZE=/srv/.backup-freeze
KEEP=14
DAY=$(date +%F)
LOG=/srv/state/backup.log
exec >>"$LOG" 2>&1
say() { echo "$(date '+%F %T')  $*"; }

say "== backup $DAY"
# A still copy, hard links on the same disk: seconds, under the hand-off's lock,
# so no hand-off is half in it. Hand-offs replace files by rename, so the links
# keep tonight's version.
rm -rf "$FREEZE"
flock /srv/state/stage.lock cp -al "$STAGE" "$FREEZE" || { say "freeze FAILED"; exit 1; }

PREV=$($SSH $BOX ls motdang/src 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | grep -v "^$DAY$" | sort | tail -1)
LINK=()
[[ -n "$PREV" ]] && LINK=(--link-dest="../$PREV")
$SSH $BOX mkdir -p motdang/src motdang/state 2>/dev/null
if rsync -a --delete --timeout=600 -e "$SSH" "${LINK[@]}" "$FREEZE/" "$BOX:motdang/src/$DAY/"; then
  say "source copied to motdang/src/$DAY${PREV:+ (linked to $PREV)}"
else
  say "source copy FAILED"; rm -rf "$FREEZE"; exit 1
fi
rm -rf "$FREEZE"
rsync -a --timeout=600 -e "$SSH" --exclude '*.lock' /srv/state/ "$BOX:motdang/state/" \
  && say "state copied" || say "state copy FAILED"

# Oldest out beyond KEEP.
$SSH $BOX ls motdang/src 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' | sort | head -n -$KEEP |
  while read -r old; do $SSH $BOX rm -rf "motdang/src/$old" && say "removed $old"; done
say "== done"
