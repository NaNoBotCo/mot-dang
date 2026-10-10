#!/bin/zsh
# server_walk.sh — motdang-build's half of the walk. importers/server_link.sh
# is the laptop's half: it sends the source to /srv/mot-dang.in and writes a
# new id into .handoff. Every five minutes (systemd motdang-walk.timer, user
# nan) this looks for an id it has not tried, copies the staging folder into
# /srv/mot-dang, and runs importers/publish_steps.sh — the same build, gates
# and deploy the laptop ran.
#
#   /srv/state/attempted   last hand-off tried     /srv/state/published  last one live
#   /srv/state/mirrored    last one the laptop copied back
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
export MD_BUILD_TIMEOUT=${MD_BUILD_TIMEOUT:-180m}
export MD_PROFILE=${MD_PROFILE:-$SSTATE/build-profile.json}   # build_sampler.py
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

# Give the laptop its copy of the last publish before docs/ is rebuilt.
PUB=$(cat "$SSTATE/published" 2>/dev/null)
if [[ -n "$PUB" && "$PUB" != "$(cat $SSTATE/mirrored 2>/dev/null)" ]] \
   && [[ -n $(find "$SSTATE/published" -mmin -30 2>/dev/null) ]]; then
  exit 0
fi

exec 8>"$SSTATE/docs.lock"; flock 8
say "== hand-off $HAND"
flock "$SSTATE/stage.lock" rsync -a --delete --exclude /docs/ --exclude /docs.next/ \
  --exclude /docs.prev/ --exclude /cache/build.lock --exclude /.handoff "$STAGE/" "$REPO/" \
  || { say "copy from staging FAILED"; note "failed" "staging copy"; exit 1 }
print -- "$HAND" > "$SSTATE/attempted"
cd "$REPO" || exit 1
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

source importers/publish_steps.sh
print -- "$HAND" > "$SSTATE/published"
say "== published $HAND — $COUNT files"
note "published" "$HAND $COUNT files"
