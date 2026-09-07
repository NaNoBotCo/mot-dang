# WO-41 — the freshness contract · Phase 0 discovery · 2026-08-28

The work order's brief: eliminate stale-data display as a class, not per feed.
Phase 0 says report before fixing. This is that report. Verdict up front:
**all four diagnosed symptoms verified on the real tree — two with sharper
mechanisms than the order assumed — and about a third of the ordered
machinery already exists under house names.** The order's frame (GitHub
Actions, workflow history, GitHub issues, CI) does not match this repo's
machinery (launchd + two walks + a ledger, R2, no remote); every phase maps
cleanly onto the real machinery and the mapping is written down here.

## The four symptoms, verified

**1. Events — worse than stale: EMPTY, by two separate defects.**
`data/events.json` = `{"generated": "2026-08-24", "count": 0, "events": []}`.
- *Defect A (Aug 24):* a harvest run completed with zero rows and WROTE the
  empty basket over the last good file (69 events, committed 2026-08-17).
  `harvest_events.py` main() writes unconditionally — no min-rows guard, no
  keep-previous-on-empty.
- *Defect B (Aug 25 → today):* every run since CRASHES —
  `parse_tribe():202 doc.get("events")` raises AttributeError because `doc`
  is a **17 MB JSON list**: the OBEC school register. Root cause: the events
  harvester selects sources from the SHARED `data/sources.json` registry by
  `method == "json"` alone, and later orders (schools, weather, cannabis)
  registered non-event sources there. The per-source isolation exists but
  its net is `(URLError, HTTPError, OSError)` — a parse-shape error escapes
  and kills the whole batch. So the empty Aug-24 file just stands.
- The morning walk DID notice: `watch_data.py` has printed
  "events.json is hollow — expected at least 1" into the log every morning
  since Aug 25. Advisory only; nothing acts on it. The order's thesis —
  "monitoring with no alerting attached" — is witnessed verbatim.
- Answer to the order's (a)/(b)/(c): **Aug 24 = (c) fired, succeeded, zero
  rows. Aug 25 onward = (b) fired and errored.** Different fixes, as the
  order says.

**2. Lottery — false staleness, exactly as diagnosed.** `lottery.json`:
fetched 2026-08-17, draw 2026-08-16 — the current draw; next is ~1 Sep. The
data is valid and the age-chip vocabulary has no way to say so. One house
rule to carry into the fix: `make_lottery.py` deliberately records **no
next-draw date** ("a date the source has not confirmed is a date this file
does not carry" — GLO publishes no schedule endpoint, and draws shift around
New Year and royal days). So the chip the order sketches ("next 1 Sep") must
render the tilde convention: "ผลงวด 16 ส.ค. · งวดต่อไป ~1 ก.ย." — the ~
marking computed-not-confirmed, per the house calendaring rule.

**3. "Coming up" showing Mother's Day on Aug 28 — verified on today's built
homepage,** and the mechanism is exactly as diagnosed:
`festivals_layer.py coming_up()` computes month distance
(`(m - today.month) % 12`) — month granularity, so a fixed-date festival
whose day has passed stays "coming up" for the rest of its month — and bakes
`เดือนนี้ · this month` at build. Two orthogonal bugs, as the order says.
One correction to the order: **the chips are NOT build-time relative** —
build.py:3491-3502 computes every `X ชม.ที่แล้ว / Xh ago` in the browser
(the code's own comment: "a baked 'today' would rot, a computed
'3 ชม.ที่แล้ว' cannot"). The panel is the baked-relative offender; the chips'
sin is 4b (age-as-staleness), not 4a.

**4. Gold one cycle behind — structural, confirmed.** `finance.json` is
fetched at 07:10 by the morning walk only; gold's `asOf` is yesterday
17:11 (the Gold Traders Association's last posting before this morning's
fetch). The standing walk refreshes ONLY weather + air intraday; finance has
no afternoon pass. Crypto same file, same 07:10-only — ~10 h old by evening,
matching the chip.

## Item 1 — every feed the site renders

External feeds (fetcher → file → main consumers):

| feed | source | fetcher | file | consumers | when fetched |
|---|---|---|---|---|---|
| weather | Open-Meteo forecast (keyless, 15 cities, one call) | make_weather.py | weather.json | widget wall tile, my.html | morning + standing walk (pre-build) |
| air | Open-Meteo air-quality API | make_air.py | air.json | AQI tile | morning + standing walk |
| showtimes | Major (recipe in ~/.mot-dang-showtimes.json, out of repo) | make_showtimes.py | showtimes.json | cinema tile | morning |
| lottery | GLO `POST /api/lottery/getLatestLottery` (first-party, keyless) | make_lottery.py | lottery.json | หวย tile + page | morning; file changes only when a new draw lands (byte-identical rewrite is skipped by design) |
| fx / gold / crypto | frankfurter.app (ECB) · goldtraders.or.th `GoldPrices/Latest` · CoinGecko | make_finance.py | finance.json | finance tile | morning ONLY ← the gold gap |
| events | data/sources.json entries yielding events: 3 Meetup iCal groups + Payap LLL tribe API | harvest_events.py | events.json + contact_leads.json | /events.html, homepage carousel, whats-on bands on place pages | morning (`--refetch`) — CRASHING since Aug 25 |
| festival dates | official announcements (PRD Chiang Mai et al.) | harvest_festivals.py | festival_dates.json → festival_calendar.json | festival pages, coming-up 📌 lines | morning, STALE_DAYS-gated |
| claims / toilet reports / suggestions | the site's own worker KV | sync_claims / sync_toilets / sync_suggestions | claims.json, toilet_reports.json, _incoming/ | place pages, /toilets | morning (keep-on-fail by design) |
| wichaa instruments | wichaa.net screenshots | make_widget_shots.py | widget_shots.json + assets | sky tile | morning (daily) |
| link health | own sweep of outbound URLs | check_links.py | linkhealth.json | reach blocks, publish gate | slow sweep, 30-day staleness |

Deterministic bakes (no external source, cannot go stale in the ingest
sense, but CAN drift as build-relative pages): horo.json, shuffle/katha/
psalms, fortune.json, sky.json (60-day bakes), open_lamps, streets.

Two loose ends found in passing: `importers/make_ticker.py` (the CM-news
RSS ticker) is **in no walk's roster** — dormant; and several fetcher
User-Agent strings still advertise `github.com/NaNoBotCo/mot-dang`,
post-divorce leftovers worth a sweep.

## Item 2 — schedules, real machinery, real outcomes

No GitHub Actions exist and none should be reported on. The machinery:

- `net.motdang.morning-walk.plist` — 07:09 ICT daily (launchd runs local
  time; no UTC offset trap on this machine). The GATHER: every fetcher above,
  then `watch_data.py`, then build+gates+publish *if the tree is quiet*.
  Log: `~/Library/Logs/motdang-morning-walk.log`.
- `net.motdang.standing-walk.plist` — every 20 min, forever. The PUBLISH:
  fingerprint gate (`walk_fingerprint.py` vs `cache/last-published.json`),
  weather+air refetch after the decision to build, full gate suite, R2
  deploy. Ledger: `cache/standing-walk.jsonl`, one verdict per round.
- Last 22 standing rounds (today): 3 published (07:25, 12:47, 15:33),
  1 failed (14:10, publish gate — healed next round), rest stood down
  "nothing new" / one timed rest. Healthy.
- Morning walk, last 8 days: gather succeeds daily; its OWN build step has
  deferred every day ("another walk holds the lock" ×3 — the 07:09 start
  collides with a standing round — or "source files are mid-task" ×5, the
  tree being perpetually mid-order). By design the standing walk ships the
  gathered data later, so nothing is lost — but it means the morning walk's
  commit step (the only auto-commit) has not run in ≥8 days either.
- The order's Phase-5 heartbeat ("fail if last build > 26 h") maps to: a
  launchd check reading the standing ledger's last `published` line. The
  escalation path (Phase 3's "GitHub issue") maps to the shared task board
  (Trello via Task tools) or a `cache/stale-feeds/` flag the walks surface —
  decision belongs to Phase 3, noted here so nobody builds an issue-opener
  against a remote that is gone.

## Item 3 — events history, 14 days

Answered above under symptom 1: through Aug 23 healthy (69 rows committed
Aug 17); Aug 24 completed-with-zero and overwrote; Aug 25–28 crashed daily
on the OBEC list; file untouched since Aug 24 08:53; watch_data shouting
into an empty room since Aug 25.

## Item 4 — every relative-time generation site

Client-side (correct already): the age chips — `md.js` block at
build.py:3491-3502 (นาที/ชม./วัน ที่แล้ว, เมื่อวาน) computed from data-ts
attributes in the reader's browser.

Baked at build (true on build day, drift after):
- `festivals_layer.py:759` — `เดือนนี้/เดือนหน้า` in coming_up. **The
  target of today's fix.**
- build.py:9492 — cinema tile "วันนี้ยังไม่มีรอบ / no times listed today".
- build.py:9602/9687/9707 — the today/wheel module headings ("วันนี้…").
- cooking_layer.py:223 — "วันนี้เรียนที่ไหนได้ / Which class today".
- festivals_layer.py:630 — "วันนี้อะไรปิด / What is shut" (festival-day
  section; contextual, verify before touching).
These stay true only while the walks rebuild daily; they are the Phase-4a
worklist, each needing a look at whether its data is per-day-selected
client-side already (the cinema tile got exactly that repair once — see
morning_walk.sh's header).

## Item 5 — can an ingest overwrite good data with empty?

| fetcher | write pattern | verdict |
|---|---|---|
| harvest_events | unconditional write of whatever survived the loop | **YES — proven Aug 24.** No min-rows, no keep-on-empty |
| make_weather | builds full doc then one write; a failed call raises first | empty-but-200 could write hollow; watch_data catches at 2 days |
| make_finance | partial guards (`if not coins`, `if not fx`) | mixed — gold/fx/crypto degrade per-section; verify per-section keep-previous in Phase 2 |
| make_showtimes | snapshot-first, validation noted in CLAUDE.md history | previously wrote 0-cinema files (the Aug-16 incident) — re-verify guard in Phase 2 |
| make_lottery | validates sheet, keeps disk on fail, byte-identical skip | good — the model the others should follow |
| sync_claims / sync_toilets | keep-what-is-on-disk when worker unreachable | good by design |
| harvest_festivals | announced-only, STALE_DAYS | good |

## What already exists that the order re-specifies

**`importers/watch_data.py` is the manifest's embryo** — per-feed roster
with cadence-aware max-age ("max_age follows how often the SOURCE really
changes": lottery 35 days, linkhealth 45, sky 60) and hollow-checks, born
from the 2026-08-16 triple-empty incident its docstring records. What it
lacks vs the order: sidecar meta (consecutive_failures, sources_ok/failed),
degrade-rendering, any consumer beyond a log line, and draw-day semantics
for the CHIP rather than the checker. **Phase 1 should grow this file into
the manifest, not stand a second roster beside it** — two rosters drift,
and this repo already has the one-copy rule for exactly that.

What the later phases need to keep working with:
- Lottery next-draw dates render with ~ (computed, unconfirmed) — the
  fetcher's presence-only rule stands.
- `festival_dates.json` keeps "a rule is not a date" — no lunar
  inference; announced instances only. The order's "resolved date for Tan
  Kuay Salak" therefore means *announced-or-held-out*, which is what the
  candidate/announced machinery already does; unannounced movables go to the
  order's own "later this year" list rather than gaining invented dates.
- No GitHub anything; escalation lands on the task board or in cache/ flags.
- stdlib only; no external status services.

## Shipping today (green-lit by the order's own sequencing): 4d + 4e

- coming_up() moves from month-distance to resolved dates: announced
  instances filtered by `date_end >= today` (multi-day stays till it ends);
  fixed-date festivals gain a machine-readable `day` in data/festivals.json
  (taken from their own window text, never invented) and roll forward past
  their date (Mother's Day → 12 Aug next year, automatically); unresolved
  movables leave "Coming up" for an "around this time of year" line — the
  order's separate list, in this site's voice.
- Server text goes absolute (the no-JS floor is always true); the baked
  เดือนนี้/เดือนหน้า literals leave the panel entirely.
- Each row carries `data-until`; `md.js` drops rows past their end at load
  and hides an emptied card — the panel self-corrects even if every walk
  stops (the order's test 6, scoped to this panel).
- Tests: tests/test_freshness.py — frozen-clock selection (Aug 28 excludes
  Mother's Day, keeps the Akha window), no relative literals in the built
  panel, data-until present and ISO-dated, homepage injection intact.

Phases 1–3, 4a–c, 5, 6 wait on Nan's numbered go, with the mapping above.
