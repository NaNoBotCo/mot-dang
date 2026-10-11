#!/bin/bash
# WO-58 finisher — waits for the harvests and crawls still running, folds what
# they find, and builds once. Written because four CMHY jobs (motorbike,
# water-gas, coworking, funeral) and three Overpass groups (utilities, driving,
# optician) were still fetching when the first build went out, and a fetch that
# lands with nobody to fold it is a fetch that never happened.
#
# Safe to run twice: every step is snapshot-first and the record upsert never
# writes an id it already holds.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
export LANG=en_US.UTF-8
say() { printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }

say "waiting for the CMHY re-harvest (motorbike · water-gas · coworking · funeral · lab)…"
for i in $(seq 1 240); do
  pgrep -f "cmhy.py" >/dev/null || break
  sleep 30
done

for j in motorbike water-gas coworking funeral; do
  if [ -s "cache/cmhy/$j/places.json" ] && [ "$(wc -c < "cache/cmhy/$j/places.json")" -gt 2 ]; then
    say "register: $j"
    python3 importers/build_trade_registers.py "$j"
  else
    say "SKIP $j — its harvest came back empty (see cache/cmhy/chain2.log)"
  fi
done

say "waiting for the Overpass groups (utilities · driving · optician)…"
for i in $(seq 1 240); do
  pgrep -f "crawl_overpass.py" >/dev/null || break
  sleep 30
done
for g in utilities driving optician; do
  for p in cm cr; do
    [ -f "cache/overpass/$p/$g.json" ] && say "  have cache/overpass/$p/$g.json"
  done
done

say "import…"
python3 importers/import_all.py > cache/import_finish.log 2>&1 || say "import FAILED — see cache/import_finish.log"
grep -E "^cm: [0-9]+ records|^cr: [0-9]+ records" cache/import_finish.log | cut -c1-60

say "lens audit…"
python3 importers/audit_lens.py || say "LENS AUDIT FAILED — a register would print a wrong page"

say "waiting for the build lock…"
while [ -f cache/build.lock ] && kill -0 "$(head -1 cache/build.lock 2>/dev/null)" 2>/dev/null; do sleep 20; done
say "build…"
python3 build.py > cache/build_finish.log 2>&1 || say "BUILD FAILED — see cache/build_finish.log"
grep -E "^built" cache/build_finish.log

say "gates…"
python3 tests/test_publish_gate.py 2>&1 | tail -3
python3 importers/audit_ot.py > /dev/null 2>&1 && say "audit_ot green"
say "done"
