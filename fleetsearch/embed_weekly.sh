#!/bin/zsh
# embed_weekly.sh — Sundays 05:00 (launchd com.nanobotco.find-embed, C147 answered
# (b) 2026-10-13). Runs embed.py, incremental: pages whose text has not changed
# since the last run are skipped, so a week of new pages costs pennies. One row
# per run in ~/.claude/state/find-embed.tsv. Skips while a D1 load is running.
# Needs the Mac: wrangler's sign-in (cfauth) is the only Cloudflare credential
# for D1 and Vectorize, and it is not on motdang-build.
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
cd "${0:A:h}/.." || exit 1
TSV="$HOME/.claude/state/find-embed.tsv"
[[ -f "$TSV" ]] || printf 'date\tminutes\tresult\n' > "$TSV"
if pgrep -f 'fleetsearch/(crawl|thumbs|load)\.py' >/dev/null; then
  printf '%s\t\tskipped: a search load is running\n' "$(date +%F)" >> "$TSV"; exit 0
fi
t0=$(date +%s)
out=$(/opt/homebrew/bin/python3.13 -u fleetsearch/embed.py 2>&1); rc=$?
t1=$(date +%s)
last=$(print -r -- "$out" | tail -1 | tr '\t' ' ' | cut -c1-160)
if (( rc == 0 )); then res="ok: $last"; else res="failed: $last"; fi
printf '%s\t%s\t%s\n' "$(date +%F)" "$(( (t1 - t0) / 60 ))" "$res" >> "$TSV"
print -r -- "$out" | tail -20
exit $rc
