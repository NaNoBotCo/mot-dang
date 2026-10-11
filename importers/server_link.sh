# server_link.sh — the laptop's half of building on motdang-build.
# Sourced by standing_walk.sh; acts only while cache/build-on-server exists.
#
#   hand_to_server       source → /srv/mot-dang.in, then a new id in .handoff and,
#                        in .handoff-at, when the copy began (UTC): the publish
#                        leaves alone live files uploaded after it
#   push_rest            cache/walk-rest mirrored to /srv/state/walk-rest
#   (no copy-back: the server's docs/ stays on the server, her word 2026-10-10)
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

# _incoming/enrich/ and the path enrich.py reads (cache/enrich_archive.txt) stay on this Mac.
HANDOFF_EXCLUDES=(--exclude /docs/ --exclude /docs.next/ --exclude /docs.prev/
  --exclude __pycache__/ --exclude '*.pyc' --exclude /cache/build.lock
  --exclude /cache/walk-rest --exclude /_incoming/enrich/ --exclude /cache/enrich_archive.txt --exclude /.claude/
  --exclude .DS_Store
  # Mapillary street photos are harvested on the server, into the staging
  # folder, and held there only (her word 2026-10-11: rented storage, not the
  # Mac). Excluded, so this mirror neither sends nor deletes them; her own
  # photos in assets/streetphotos/own/ still travel.
  --exclude '/assets/streetphotos/*.jpg' --exclude /data/street_photos.json)

hand_to_server() {
  local id at; id="$(date +%Y%m%dT%H%M%S)-$$"; at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  "${SSH[@]}" "$SERVER" "mkdir -p $STAGE $SSTATE" || return 1
  # What is live, as far as this Mac knows: the server checks its build against it.
  (cd docs && find . -type f ! -path './tiles/*' | sed 's#^\./##' | sort) | gzip > cache/docs-list.txt.gz
  # The code of HEAD rides beside the folder; the server puts it over the
  # folder's code (importers/build_code.py). Without the flag the folder's own
  # code is built, as before.
  if [[ -f cache/build-from-commit ]]; then
    local commit left
    commit=$(python3 importers/build_code.py pack cache/build-code.tar) \
      || { say "could not pack the committed code"; return 1 }
    left=$(python3 importers/build_code.py left-out 2>/dev/null)
    say "code from commit ${commit:0:10}"
    [[ "$commit" == "$(git rev-parse HEAD)" ]] \
      || { say "  ⚠️  HEAD $(git rev-parse --short=10 HEAD) does not compile (tools/codecheck.py HEAD); sent the newest commit that does"
           note "code-held-back" "HEAD $(git rev-parse --short=10 HEAD) does not compile" }
    if [[ -n "$left" ]]; then
      say "  not committed, so not built ($(print -- "$left" | grep -c .)):"
      print -- "$left" | head -12 | while read -r l; do say "    $l"; done
    fi
  else
    rm -f cache/build-code.tar
  fi
  rsync -a --delete --partial $RSYNC_IDLE "${HANDOFF_EXCLUDES[@]}" -e "${SSH[*]}" \
    --rsync-path="flock $SSTATE/stage.lock rsync" ./ "$SERVER:$STAGE/" || return 1
  "${SSH[@]}" "$SERVER" "flock $SSTATE/stage.lock sh -c 'echo $at > $STAGE/.handoff-at && echo $id > $STAGE/.handoff'" || return 1
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

