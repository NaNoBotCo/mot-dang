# server_link.sh — the laptop's half of building on motdang-build.
# Sourced by standing_walk.sh; acts only while cache/build-on-server exists.
#
#   hand_to_server       source → /srv/mot-dang.in, then a new id in .handoff
#   push_rest            cache/walk-rest mirrored to /srv/state/walk-rest
#   mirror_from_server   after a server publish, its docs/ back into docs/ here,
#                        so /find's reload and --files publishes read what is live.
#                        The server holds docs.lock while it builds, and waits
#                        up to 30 minutes after a publish for this copy before
#                        it starts the next build.
#
# The server copies the staging folder into its working tree only between
# builds, under the same flock as the hand-off, so a build never reads a
# half-sent tree. Its side is importers/server_walk.sh.

SERVER="nan@motdang-server"
SRV=/srv/mot-dang
STAGE=/srv/mot-dang.in
SSTATE=/srv/state
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=20)
# An idle limit on every transfer. On 2026-10-10 the copy-back stalled on one
# file with nothing arriving for minutes; macOS's rsync (openrsync) does not give
# up on its own, so the walk round never reached its import or hand-off, and the
# shared docs.lock it held on the server would have kept the next build waiting.
RSYNC_IDLE=--timeout=300

# _incoming/enrich/ is read from the Legal Cases export and stays on this Mac.
HANDOFF_EXCLUDES=(--exclude /docs/ --exclude /docs.next/ --exclude /docs.prev/
  --exclude __pycache__/ --exclude '*.pyc' --exclude /cache/build.lock
  --exclude /cache/walk-rest --exclude /_incoming/enrich/ --exclude /.claude/
  --exclude .DS_Store)

hand_to_server() {
  local id; id="$(date +%Y%m%dT%H%M%S)-$$"
  "${SSH[@]}" "$SERVER" "mkdir -p $STAGE $SSTATE" || return 1
  # What is live, as far as this Mac knows: the server checks its build against it.
  (cd docs && find . -type f ! -path './tiles/*' | sed 's#^\./##' | sort) | gzip > cache/docs-list.txt.gz
  rsync -a --delete --partial $RSYNC_IDLE "${HANDOFF_EXCLUDES[@]}" -e "${SSH[*]}" \
    --rsync-path="flock $SSTATE/stage.lock rsync" ./ "$SERVER:$STAGE/" || return 1
  "${SSH[@]}" "$SERVER" "flock $SSTATE/stage.lock sh -c 'echo $id > $STAGE/.handoff'" || return 1
  say "sent to the server as $id"
}

push_rest() {
  [[ -f cache/build-on-server ]] || return 0
  if [[ -f "$REST" ]]; then
    rsync -a $RSYNC_IDLE -e "${SSH[*]}" "$REST" "$SERVER:$SSTATE/walk-rest" 2>/dev/null \
      || say "⚠️  could not tell the server the walk is resting"
  else
    "${SSH[@]}" "$SERVER" "rm -f $SSTATE/walk-rest" 2>/dev/null || true
  fi
}

MIRRORED=""
mirror_from_server() {
  [[ -f cache/build-on-server ]] || return 0
  local pub mine
  pub=$("${SSH[@]}" "$SERVER" "cat $SSTATE/published 2>/dev/null") || return 0
  mine=$(cat cache/server-mirrored 2>/dev/null)
  [[ -z "$pub" || "$pub" == "$mine" ]] && return 0
  say "the server published $pub — copying its docs/ back"
  rsync -a --delete-delay $RSYNC_IDLE --exclude /tiles/ -e "${SSH[*]}" \
    --rsync-path="flock -s -n $SSTATE/docs.lock rsync" "$SERVER:$SRV/docs/" docs/ \
    || { say "docs/ not copied back — the server is building; next round tries again"; return 0 }
  print -- "$pub" > cache/server-mirrored
  "${SSH[@]}" "$SERVER" "echo $pub > $SSTATE/mirrored" || true
  MIRRORED=1
}
