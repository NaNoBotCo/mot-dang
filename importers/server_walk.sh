#!/bin/zsh
# server_walk.sh — motdang-build's half of the walk. importers/server_link.sh
# is the laptop's half: it sends the source to /srv/mot-dang.in and writes a
# new id into .handoff. Every five minutes (systemd motdang-walk.timer, user
# nan) this looks for an id it has not tried, copies the staging folder into
# /srv/mot-dang, and runs importers/publish_steps.sh — the same build, gates
# and deploy the laptop ran.
#
#   /srv/state/attempted   last hand-off tried     /srv/state/published  last one live
#   /srv/state/walk-rest   the laptop's cache/walk-rest, sent each round
#   ~/motdang-server-walk.log, /srv/state/walk.jsonl
set -u
export PATH=/usr/local/bin:/usr/bin:/bin
REPO=/srv/mot-dang
STAGE=/srv/mot-dang.in
SSTATE=/srv/state
LOG="$HOME/motdang-server-walk.log"
TOWER=/nonexistent
export MD_JOBS=${MD_JOBS:-1}
# 360 minutes: a full build was 170 minutes of one Mac core on 2026-09-10, and
# this host has two shared cores and 3.8 GB. The limit is there to end a hung
# build; at 180 it also ended slow healthy ones, every round from 2026-10-05.
export MD_BUILD_TIMEOUT=${MD_BUILD_TIMEOUT:-360m}
export MD_PROFILE=${MD_PROFILE:-$SSTATE/build-profile.json}   # build_sampler.py
export MD_LAYER_STATE=${MD_LAYER_STATE:-$SSTATE/layers.json}   # layers.py: each layer's time, outputs, failures
MISSING_CEILING=500   # 2026-10-05: an 11-hour-old source would have deleted 1,977 live files

mkdir -p "$SSTATE"
if [[ -f "$LOG" ]] && (( $(stat -c %s "$LOG") > 5242880 )); then mv -f "$LOG" "$LOG.1"; fi
exec >>"$LOG" 2>&1
exec 9>"$SSTATE/walk.lock"; flock -n 9 || exit 0

say() { print -- "$(date '+%F %T')  $*" }
note() {
  python3 - "$1" "$2" <<'PY' >>"$SSTATE/walk.jsonl" 2>/dev/null
import json, sys, time
print(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "verdict": sys.argv[1],
                  "detail": sys.argv[2]}, ensure_ascii=False))
PY
}
stand_down() { say "standing down — $1"; note "stood-down" "$1"; exit 0 }
# A layer that failed did not stop the build (layers.py); its pages are a round old.
layer_note() {
  local f; f=$(python3 -c 'import json,sys; print(", ".join(json.load(open(sys.argv[1])).get("failed", [])))' "$MD_LAYER_STATE" 2>/dev/null)
  [[ -n "$f" ]] && { say "⚠️  layers that failed, their last good pages kept: $f"; note "layers-failed" "$f" }
  return 0
}
remember_gate_fail() { say "the gate failed on hand-off $HAND; the next hand-off builds again" }

HAND=$(cat "$STAGE/.handoff" 2>/dev/null)
[[ -z "$HAND" || "$HAND" == "$(cat $SSTATE/attempted 2>/dev/null)" ]] && exit 0

# The laptop's rest holds this side too. A timestamp rests until that moment.
if [[ -f "$SSTATE/walk-rest" ]]; then
  UNTIL=$(head -1 "$SSTATE/walk-rest" | tr -d '[:space:]')
  [[ -z "$UNTIL" ]] && exit 0
  python3 - "$UNTIL" <<'PY' || exit 0
import sys, datetime
s = sys.argv[1]
s = s[:-1] + "+00:00" if s[-1:] in "Zz" else s
try:
    u = datetime.datetime.fromisoformat(s)
    u = u if u.tzinfo else u.astimezone()
    sys.exit(0 if datetime.datetime.now(datetime.timezone.utc) >= u else 1)
except Exception:
    sys.exit(1)
PY
fi

exec 8>"$SSTATE/docs.lock"; flock 8
say "== hand-off $HAND"
# A data file the laptop sent while something was still writing it does not
# parse; the working tree keeps last round's copy of it (tools/datacheck.py).
HELD=()
for f in ${(f)"$(flock "$SSTATE/stage.lock" python3 "$STAGE/tools/datacheck.py" "$STAGE" "$REPO" 2>/dev/null)"}; do
  HELD+=(--exclude "/$f"); say "  held back, does not parse: $f"
done
(( ${#HELD} )) && note "data-held-back" "$(( ${#HELD} / 2 )) file(s) that do not parse"
flock "$SSTATE/stage.lock" rsync -a --delete --exclude /docs/ --exclude /docs.next/ \
  --exclude /docs.prev/ --exclude /cache/build.lock --exclude /.handoff --exclude /.handoff-at \
  "${HELD[@]}" "$STAGE/" "$REPO/" \
  || { say "copy from staging FAILED"; note "failed" "staging copy"; exit 1 }
print -- "$HAND" > "$SSTATE/attempted"
# When the laptop began sending this source. deploy.py keeps live files
# uploaded after it: this build cannot know them (publish/safety.py,
# uploaded_since — Lanna Craft, 2026-10-10). A hand-off from before
# .handoff-at existed reads its id's wall clock 14 h early, the earliest that
# clock can mean in any zone.
MD_SOURCE_AT=$(cat "$STAGE/.handoff-at" 2>/dev/null)
if [[ -z "$MD_SOURCE_AT" ]]; then
  MD_SOURCE_AT=$(date -u -d "$(print -- "${HAND%%-*}" | sed -E 's/(....)(..)(..)T(..)(..)(..)/\1-\2-\3 \4:\5:\6/') UTC - 14 hours" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)
fi
export MD_SOURCE_AT
say "source taken ${MD_SOURCE_AT:-at an unknown time}"
cd "$REPO" || exit 1

# The laptop sent HEAD's code beside the folder (importers/build_code.py): it
# replaces the folder's code, so a file a session is still editing is not
# built. build_code.py itself is taken from the tar, not the folder.
if [[ -f cache/build-code.tar ]]; then
  tar -xOf cache/build-code.tar importers/build_code.py > "$SSTATE/build_code.py" \
    && python3 "$SSTATE/build_code.py" overlay cache/build-code.tar "$REPO" \
    || { say "could not put the committed code in place"; note "failed" "code overlay"; exit 1 }
  say "code from commit $(git get-tar-commit-id < cache/build-code.tar | cut -c1-10)"
fi
TODAY=$(date +%F)

# Live is what the bucket holds, listed at publish time by the same call
# deploy.py's deletion preview makes (publish/safety.py). Until 2026-10-10 the
# list came from the laptop's own docs/, which stops matching the bucket once
# the laptop no longer builds: that day it carried 1,340 place pages the live
# site answers 404 for, enough to refuse any build.
pre_deploy() {
  local n rc
  python3 - "$SSTATE/missing.txt" <<'PY'
import sys
sys.path.insert(0, "publish")
try:
    import deploy, safety
    gone = safety.deletions_preview("R2:%s" % deploy.BUCKET,
                                    deploy.rclone_env(deploy.creds()), deploy.run)
except BaseException as e:
    print("bucket listing failed: %r" % (e,))
    sys.exit(2)
with open(sys.argv[1], "w") as fh:
    fh.write("".join(k + "\n" for k in gone))
PY
  rc=$?
  if (( rc != 0 )); then
    say "REFUSING — could not list the live bucket to compare against"
    note "failed" "bucket listing"
    return 1
  fi
  n=$(wc -l < "$SSTATE/missing.txt")
  say "$n live file(s) not in this build"
  if (( n > MISSING_CEILING )); then
    awk -F/ '{print $1"/"$2}' "$SSTATE/missing.txt" | sort | uniq -c | sort -rn | head -8
    say "REFUSING — over $MISSING_CEILING; the list is $SSTATE/missing.txt"
    note "failed" "$n live files missing from the build"
    return 1
  fi
}

# --- the last good code ----------------------------------------------------
# A session can leave build.py or a layer half-edited when the walk sends the
# tree; the build or a gate then fails and the site stops updating until
# someone notices (58 failures that way, 2026-09-20 to 10-05). So every
# publish keeps a copy of the code it was built from, and a hand-off whose code
# fails is built once more with that code and the hand-off's own data. Code:
# the Python, shell and JS that build, gate and publish, and data/curated.
LAST_GOOD="$SSTATE/last-good"
CODE_FILTER=(--exclude __pycache__/ --exclude node_modules/ --exclude .wrangler/
  --exclude hf-dataset/ --include '/*.py' --include /assets/ --include '/assets/*.js'
  --include /data/ --include '/data/curated/***' --include '/importers/***'
  --include '/publish/***' --include '/tests/***' --include '/tools/***'
  --include '/fleetsearch/***' --include '/worker/***' --include '/worker-tt/***'
  --exclude '*')

# The publish runs in a subshell: publish_steps.sh exits on any failure, and
# this side has to see it to try the last good code.
publish_once() {
  rm -f "$SSTATE/.publish-ok"
  ( source importers/publish_steps.sh && print -- "$COUNT" > "$SSTATE/.publish-ok" )
  [[ -s "$SSTATE/.publish-ok" ]]
}

if publish_once; then
  COUNT=$(cat "$SSTATE/.publish-ok")
  rsync -a --delete "${CODE_FILTER[@]}" "$REPO/" "$LAST_GOOD/" \
    && print -- "$HAND" > "$LAST_GOOD/.handoff" \
    || say "⚠️  could not keep this publish's code as the last good copy"
  print -- "$HAND" > "$SSTATE/published"
  say "== published $HAND — $COUNT files"
  note "published" "$HAND $COUNT files"
  layer_note
  exit 0
fi

VERDICT=$(tail -1 "$SSTATE/walk.jsonl" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("verdict",""))' 2>/dev/null)
WHY=$(tail -1 "$SSTATE/walk.jsonl" | python3 -c 'import json,sys; print(json.loads(sys.stdin.read()).get("detail",""))' 2>/dev/null)
[[ "$VERDICT" == "failed" ]] || exit 0      # stood down, not failed
# The upload and the bucket listing fail for reasons code does not cause.
case "$WHY" in
  deploy.py*|"bucket listing") exit 1 ;;
esac
GOOD=$(cat "$LAST_GOOD/.handoff" 2>/dev/null)
if [[ -z "$GOOD" || "$GOOD" == "$HAND" ]]; then
  say "no earlier good code to fall back on — nothing published"
  exit 1
fi
say "the code of $HAND failed ($WHY); building again with the code of $GOOD and the data of $HAND"
rsync -a --exclude /.handoff "$LAST_GOOD/" "$REPO/" \
  || { say "could not restore the last good code"; note "failed" "restore last good code"; exit 1 }
if publish_once; then
  COUNT=$(cat "$SSTATE/.publish-ok")
  print -- "$HAND" > "$SSTATE/published"
  say "== published $HAND with the code of $GOOD — $COUNT files; the newer code failed: $WHY"
  note "published-last-good-code" "$HAND data, $GOOD code, $COUNT files; newer code failed: $WHY"
  layer_note
  exit 0
fi
note "failed" "the last good code failed too ($WHY)"
exit 1
