# search_reload.sh — defines search_reload(). Sourced by standing_walk.sh.

# --- the search follows the publish ----------------------------------------
# motdang.net/find answers from its own index (fleetsearch/README.md), which
# only a reload brings up to date: on 2026-10-03 nothing published after the
# 10-02 04:07 load could be found, and the nightly task that was to reload it
# runs only while the desktop app is open. So the round that published reloads
# it. The README's rules: never while a build is running (the crawl reads each
# place's .json twin, which a build in flight has not written), and a D1 load
# that stops is resumed once from the chunk it names. /find answers 500s in
# bursts while chunks import. One row per reload in ~/.claude/state/search-reload.tsv,
# the same file the nightly task writes; the nightly stands down when this
# reloaded within 20 hours. A failed reload costs a stale search, never the
# publish above.
RELOAD_TSV="$HOME/.claude/state/search-reload.tsv"
reload_row() {   # reload_row <gap start> <gap end> <minutes> <pages> <result>
  [[ -f "$RELOAD_TSV" ]] || printf 'date\tgap_start\tgap_end\tminutes\tpages\tresult\n' > "$RELOAD_TSV"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$1" "$2" "$3" "$4" "$5" >> "$RELOAD_TSV"
}
search_reload() {
  local held="" pages out rc from g0 g1 t0 t1
  if [[ -f cache/build.lock ]]; then
    held=$(head -1 cache/build.lock 2>/dev/null | tr -d '[:space:]')
    [[ -n "$held" ]] && ! kill -0 "$held" 2>/dev/null && held=""
  fi
  if [[ -n "$held" ]] || ps -eo args | grep -E '[b]uild\.py$' >/dev/null; then
    say "search reload skipped — a build is running"; reload_row "" "" "" "" "skipped: build running"; return 0
  fi
  if ps -eo args | grep -E '[f]leetsearch/(crawl|thumbs|load)\.py' >/dev/null; then
    say "search reload skipped — another reload is running"; return 0
  fi
  say "search: crawling the fleet"
  python3 -u fleetsearch/crawl.py || { say "⚠️  search crawl FAILED — /find keeps the last index"; reload_row "" "" "" "" "failed at step 2: crawl.py"; note "search-reload" "failed: crawl"; return 1 }
  pages=$(python3 -c "import json; print(json.load(open('cache/fleetsearch/crawl.json'))['pages'])" 2>/dev/null)
  python3 -u fleetsearch/thumbs.py --upload || say "⚠️  search thumbnails kept the last set — new rows go without a picture"
  g0=$(date +%H:%M); t0=$(date +%s)
  out=cache/fleetsearch/reload-walk.log
  python3 -u fleetsearch/load.py 2>&1 | tee "$out"; rc=${pipestatus[1]}
  if (( rc != 0 )); then
    from=$(grep -oE -- '--from [0-9]+' "$out" | tail -1 | grep -oE '[0-9]+')
    if [[ -n "$from" ]]; then
      say "search load stopped at chunk $from — resuming once"
      python3 -u fleetsearch/load.py --remote --from "$from" 2>&1 | tee "$out"; rc=${pipestatus[1]}
    fi
  fi
  g1=$(date +%H:%M); t1=$(date +%s)
  if (( rc != 0 )); then
    say "⚠️  search load FAILED — $(tail -1 "$out")"
    reload_row "$g0" "$g1" "$(( (t1 - t0) / 60 ))" "${pages:-}" "failed at step 4: $(tail -1 "$out" | tr '\t' ' ' | cut -c1-160)"
    note "search-reload" "failed: load.py"
    return 1
  fi
  reload_row "$g0" "$g1" "$(( (t1 - t0) / 60 ))" "${pages:-}" "ok · walk"
  say "search reloaded — ${pages:-?} pages, /find gap $g0–$g1"
  note "search-reload" "ok: ${pages:-?} pages"
}
