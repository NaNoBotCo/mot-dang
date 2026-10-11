#!/usr/bin/env python3
"""WO-111. The engineers' build-notes page, /build-notes.html.

Content is data: SECTIONS holds each section's Thai and English heading and its blocks. Every figure
carries its date in the text, and each was checked against a file in this repository on 2026-10-11.
Backticks mark code. Paragraphs are English; headings and table headers are Thai and English, as on the
rest of the site. body() returns the page body, which colophon_layer.emit() places inside page().
plain() is the same content as plain text.
"""
import html
import re

TITLE = ("บันทึกการสร้าง", "Build notes")
LEDE = ("มดแดงสร้างและเดินระบบอย่างไร สำหรับวิศวกร ตัวเลขทุกตัวมีวันที่กำกับ",
        "How motdang.net is built and run, for engineers. Each figure carries its date.")

SECTIONS = [
    {"id": "overview", "th": "ภาพรวม", "en": "Overview", "blocks": [
        ("p", "motdang.net is a Thai-first directory of Chiang Mai and Chiang Rai. The place pages, shelf pages, front page and the index behind the public API are static files written by one Python program, `build.py`, and uploaded to an R2 bucket (Cloudflare's object storage). A Cloudflare Worker (a script that runs at Cloudflare's edge) reads the bucket and answers each request. Reader submissions go to a second Worker backed by KV (a key-value store). The search at `/find` reads a D1 database (Cloudflare's hosted SQLite)."),
        ("p", "`build.py` uses the standard library and its own modules, 98 `*_layer.py` files on 2026-10-11, one per feature area. Pillow is imported inside the functions that draw pictures. The share-card renderers also drive headless Chrome and run before the build."),
        ("table", ("ตัวเลข", "Figure", "วันที่ที่นับ", "Counted"), [
            ("88,988 places, 98,687 pages in the sitemap", "from `colophon.json` as built, 2026-10-10"),
            ("89,247 canonical records: Chiang Mai 63,743, Chiang Rai 25,504", "counted from `data/canonical/`, 2026-10-11, one build later"),
            ("`docs/` 10.4 GB in 271,090 files", "2026-10-05, from the note in `check_room()`"),
            ("`build.py` 24,400 lines; 184 importer scripts and 9 shell scripts; 157 test files", "counted in the working tree, 2026-10-11"),
        ]),
    ]},
    {"id": "data", "th": "ข้อมูลและที่มา", "en": "Data and provenance", "blocks": [
        ("p", "A record is one object in `data/canonical/cm.json` or `cr.json`: `id`, `province`, `cat` and `sub` (the shelf), `name`, `nameTh`, `nameEn`, `lat`, `lng`, `geoPrecision`, `address`, `phone`, `website`, `hours`, `attrs`, `sources`, `confidence`, `updatedAt`. The importers rewrite these files whole. Hand-kept field truth sits in `data/curated/` and wins over a crawled record with the same source reference. Researched facts go in `curated/enrich.json`, which a crawl does not overwrite."),
        ("p", "`sources` is a list. An entry has a `type`, a `ref`, usually a `via` and a fetch date, and where it applies a `licence` and a `release`. `confidence` takes six values: third-party, crawled, official, curated, field, register. `geoPrecision` takes four: exact (77,085 records on 2026-10-11), approx (6,938), needs-pin (4,849), block (375). A place page shows its provenance as a border: dashed for a crawl, solid for a mapper's tag, bold for a person who stood there."),
        ("table", ("ต้นทาง", "Source", "รายการ", "Entries"), [
            ("Overture Maps Places, release 2026-08-19.0, CDLA-Permissive-2.0", "69,459"),
            ("COD-AB administrative polygons (OCHA, Royal Thai Survey Department): which tambon and amphoe a pin falls in, derived", "69,918"),
            ("Address parsing, derived", "34,604"),
            ("OpenStreetMap through a slow Overpass crawl, ODbL", "16,017"),
            ("OpenStreetMap river lines, derived", "4,663"),
            ("National Office of Buddhism temple register", "1,376"),
            ("OBEC school register", "1,302"),
            ("data.go.th registers", "1,256"),
            ("Field entries: a person stood there (signboards, photographs); 930 records carry one", "942"),
            ("weed.th directory", "615"),
            ("CITIZENinfo (DGA)", "514"),
        ]),
        ("p", "The table counts source entries across all 89,247 records on 2026-10-11. A record carries several, so the rows do not sum to the record count."),
        ("p", "Beside the records: weather, PM2.5, river gauges (Royal Irrigation Department), fire hotspots (NASA FIRMS), showtimes, lottery results, exchange rates, events from iCal and JSON feeds, festival dates, iNaturalist sightings and Wikimedia Commons photographs. Each is an importer in `importers/` that writes a snapshot to disk and keeps the previous snapshot when its source does not answer. The build makes no network request. `importers/` is where the network is used."),
        ("p", "A crawl is not a verification. The freshness signal needs a human touch, an owner's claim or a field source, so one bulk import cannot raise it on every record. A dead official site is named and dated, and the Internet Archive copy is linked in place of the dead link; `check_links.py` runs each morning."),
        ("p", "Two crawl details. An Overpass timeout answers HTTP 200 with an empty `elements` list and the error in `remark`; with a snapshot-first crawl, caching that leaves a shelf empty for good, so `fetch()` raises `OverpassRemark`. A province is an area: provinces are clipped with `area[\"ISO3166-2\"=\"TH-50\"]`, since a rectangle around Chiang Rai returns places in Laos and Myanmar."),
    ]},
    {"id": "walks", "th": "รอบเดิน", "en": "The walks", "blocks": [
        ("p", "Two scheduled jobs on the Mac (launchd). The morning walk runs at 07:09 and gathers the daily sources: weather, air, river gauges, fire hotspots, showtimes, lottery, finance, events, festival dates and link health. It also pulls reader submissions (claims, toilet reports, suggestions) and runs a watchdog that reports a source that came home empty. It writes to disk. The standing walk runs every 20 minutes and publishes whatever is on disk."),
        ("p", "A standing-walk round runs these steps in order and stops at the first that says wait:"),
        ("ol", [
            "`cache/walk-rest` exists: rest. An empty file rests until removed; an ISO timestamp rests until then.",
            "A shared walk lock, and any `cache/build.lock` held by a live process: stand down.",
            "Source files touched in the last 10 minutes: stand down. A tree nobody has written to for ten minutes is between edits.",
            "Sync claims, toilet reports and suggestions. Import, unless a crawl is out. Rebuild the streets, the temple rounds and the opening-hours lamps.",
            "The same inputs failed the publish gate last round: stand down. `cache/gate-fail.fp` holds their hash.",
            "Change gate: `walk_fingerprint.py` hashes what a build reads, drops the `generated` stamps the writers put inside their output, and compares with `cache/last-published.json`. No change and the last publish under 20 hours old: stand down.",
            "Refresh weather, air and river gauges after that decision. Stamp `BUILD_DATE`.",
            "Hand off to the build server, or build locally when `cache/build-on-server` is absent.",
        ]),
        ("p", "The change gate exists because the first evening of the standing walk republished a byte-identical site four times in ninety minutes, the weather having been refetched at the top of each round. The quiet window replaced a clean-tree rule that let the morning walk publish on 2 mornings of 14. The walk does not commit; `cache/standing-walk.jsonl` records each round."),
        ("p", "Ledger (`cache/standing-walk.jsonl`), 2026-08-18 to 2026-10-11, counted at 14:24 Bangkok: 1,638 rounds. From 2026-09-20: 230 stood down, 150 handed to the server, 50 published from the Mac; failures were 64 in `build.py`, 47 in the import, 21 in the deploy, 17 at the publish gate and 2 in the hand-off."),
    ]},
    {"id": "server", "th": "เซิร์ฟเวอร์สร้าง", "en": "Build server", "blocks": [
        ("p", "Since 2026-10-05 the standing walk hands each round to `motdang-build`, a server with two shared cores and 3.8 GB of RAM (`importers/server_walk.sh`). Removing `cache/build-on-server` builds on the Mac again."),
        ("p", "Laptop side, `importers/server_link.sh`. `rsync` sends the source tree to a staging folder under a lock, leaving out `docs/`, `docs.next/`, `docs.prev/`, the build lock, the rest file and one private input folder. Every transfer has a 300-second idle timeout: on 2026-10-10 a stalled copy blocked a round and held a lock the next build needed. Then it writes a hand-off id and the UTC time the copy began. With `cache/build-from-commit` present it also sends the code of `HEAD` as a tar, so a half-edited file in the working tree is not built (on since 2026-10-10 19:36)."),
        ("p", "Server side, `importers/server_walk.sh`. A systemd timer starts it every five minutes. It takes the lock without waiting, looks for a hand-off id it has not tried, honours the same rest file, copies staging into the build tree under a second lock, overlays the committed code, and runs `importers/publish_steps.sh`: the same build, gates and deploy the Mac ran. One verdict line per attempt goes to `walk.jsonl`: published, failed, stood-down."),
        ("p", "After each publish the server keeps the code it built from as `last-good`. When a hand-off's build or gate fails, it is built once more with the last good code and its own data, and `walk.jsonl` says `published-last-good-code`. An upload or bucket-listing failure is not retried this way. This replaced the loss of the site's updates to a half-edited layer: 58 times between 2026-09-20 and 2026-10-05."),
        ("p", "Settings: `MD_JOBS=1` (one worker process on 3.8 GB), `MD_BUILD_TIMEOUT=360m` (a full build was 170 minutes on one Mac core on 2026-09-10; the limit was 180 minutes on the server until 2026-10-10), `MD_PROFILE` set so `build_sampler.py` records where time goes every two seconds."),
        ("table", ("ที่มาในรีโป ณ 2026-10-11", "From the repo, 2026-10-11", "ผล", "Result"), [
            ("One function re-parsing a 140 MB file for each shelf map (docstring of `_moat_pins` in `build.py`)", "about 90% of a build's time on `motdang-build`"),
            ("Emoji-to-icon sweep over page text (commit `ae3eb7afdb`)", "one range scan, 11 times faster on 400 place pages"),
            ("Settings file read on every page (comment on `ask_enabled`, commit `1757f1fb9d`)", "about 30 s on `motdang-build`, read once per process"),
            ("Writing about 180,000 place files (commit `0703a1a472`)", "444 of 1,687 s on 2026-10-11"),
        ]),
    ]},
    {"id": "build", "th": "การสร้างและ docs.next", "en": "The build and the docs.next swap", "blocks": [
        ("p", "`build.py` writes the site into `docs.next/` and renames it over `docs/` at the end (`_swap_into_place()`). Two renames, each atomic on APFS; `docs.prev/` is deleted after the swap. A build killed halfway leaves the previous whole `docs/` where the publisher looks. This came after 2026-09-08, when a half-written `docs/` was published (see Incidents)."),
        ("p", "The build holds a second copy of the site beside the first until the swap. On 2026-10-05 `docs/` was 10.4 GB in 271,090 files, and a build died with `Errno 28` after the disk reached 213 MB free. `check_room()` now measures the last `docs/` with `du` and refuses to start when free space is under that size plus 5 GB. The swap itself needs about 8 GB spare for the minute both trees exist."),
        ("p", "`cache/build.lock` holds the builder's pid. A second build refuses and names the holder; a lock whose process is gone is announced and taken. A build into a different output folder takes no lock, and the tests read `MD_DOCS`, which is how they run while another build holds `docs/`."),
        ("p", "Same inputs should give the same bytes. `PYTHONHASHSEED=0` is set in the publish steps, because an event with no uid took its calendar UID from a salted `hash()`. On 2026-10-10 a round three hours after the last changed 79,500 files, and 1,000 sampled place pages differed only in the weather and air line. That line is now filled in by `md.js` from `data/nownear.json`."),
        ("p", "The sitemap dates each page by a fingerprint of its content: 97,113 pages changed in the 2026-10-10 build and 1,572 kept an earlier date."),
    ]},
    {"id": "gates", "th": "ด่านตรวจ", "en": "Gates", "blocks": [
        ("p", "`importers/publish_steps.sh` is sourced by both walks, so the Mac and the server pass the same gates. A hard gate stops the publish and writes `failed` to the ledger. An advisory gate prints a line and the publish goes on."),
        ("table", ("ด่าน", "Gate", "ตรวจอะไร", "Checks"), [
            ("hard: `build.py`", "exit status, within 180 minutes on the Mac and 360 on the server"),
            ("hard: `test_publish_gate.py`", "no link to a URL `check_links.py` found dead; no local paths in the pages; a front page and the furniture it needs; the right domain; every site under `docs/` has a card in the register"),
            ("hard: `test_asked.py`", "a published reader question has its records, page, card and a filled reply"),
            ("hard: `test_sites.py`", "the site register"),
            ("hard: `test_map_sanity.py`", "no swapped or out-of-country pin, none off its frame or province; a ratchet, so rows known when it was added are listed and a new one fails"),
            ("hard: `test_shelflife.py`", "a perishable figure past its age is not drawn"),
            ("hard: route and front-page tests (node)", "`test_plan_routes.js`, `test_front_calendar.js`, `test_soi_run.js`"),
            ("hard: path leak and floor", "`grep` over `docs/` for local filesystem paths; at least 20,000 files"),
            ("hard, server only", "the live bucket is listed and compared; more than 500 live files missing from the build stops the publish"),
            ("advisory", "shelf cards, tags, pins, copy assurances (`test_no_assurances.py`), `llms.txt` counts, the front clock, the calendar bands"),
        ]),
        ("p", "157 test files sit in `tests/`. `test_search.py` runs the shipped JavaScript matcher under node over the page's own pipeline. `test_ground.py` reads one column down a rendered map frame and expects it to cross the moat's water exactly twice."),
    ]},
    {"id": "publish", "th": "การเผยแพร่", "en": "Publish: R2 and the Worker", "blocks": [
        ("p", "The site once deployed through Cloudflare Pages from a git host. Pages caps a project at 20,000 files and `docs/` was 27,577 at the move. R2 has no object cap, and the 116 MB basemap archive lives in the same bucket."),
        ("p", "`publish/deploy.py` wraps `rclone sync`, which makes the bucket match `docs/` and deletes what `docs/` lacks. It runs as a dry run unless given `--yes`, and takes the build lock so it cannot sync a tree a build is writing. `publish/safety.py` carries the checks that came out of the 2026-09-08 outage: a required-path set, per-subtree floors, a deletion preview built by listing both sides, a ceiling of 2,000 live objects deleted in one run, a list of prefixes never pruned (`vendor/`, `glyphs/`, `api/`), and a smoke test that asks the live origin a list of questions after the upload. `--only` and `--files` publish part of the tree. A live file uploaded after the hand-off began is kept, since the build could not know it."),
        ("p", "`publish/worker.js` serves the bucket. `.html` is served directly and the extensionless path resolves to the same object, so the common path has no redirect; some folder indexes still redirect. Range requests pass through to R2, which is all a PMTiles archive needs, and tiles carry `max-age=31536000, immutable`. Every response carries `Access-Control-Allow-Origin: *`. `/api/v1/*` is answered from a baked `index.json`, checked against the bucket by an etag request every 60 seconds (OpenAPI 3.1.0, 8 paths on 2026-10-10)."),
        ("p", "The Worker writes an Analytics Engine row for a page request: referrer host, the landing path with the query dropped, and a category derived from the User-Agent. Blob position is the schema, and `test_edge_count.mjs` fails when the order drifts from the collector it shares a dataset with."),
        ("p", "The claims Worker (`worker/worker.js`, KV) takes claims, toilet reports, thumbs and notes (`/feedback`), suggestions (`/suggest`), listing forms and tester reports. Rate limits per address per hour: 12 suggestions, 120 feedback events, 12 notes. A suggestion queue and the notes have no public GET. Importers read them with an authenticated call into `_incoming/`, which is gitignored."),
        ("p", "Backups are `git bundle` files of every repo, written by `importers/offsite_backup.py` to a separate bucket, the last three kept per repo. A backup written into the site bucket is deleted by the next deploy, which is how the first one was lost."),
    ]},
    {"id": "map", "th": "แผนที่พื้นฐาน", "en": "Map basemap", "blocks": [
        ("p", "Maps are MapLibre GL JS v5.24.0 over PMTiles (v3), a single-file tile archive read with HTTP range requests, with both the library and the archive served from the site's own origin. The archives came from a Protomaps planet build dated 2026-08-11 through `pmtiles extract`."),
        ("table", ("ไฟล์", "Archive", "ขนาด", "Size"), [
            ("`cm-cr.pmtiles`, both provinces, z0 to z15", "121,494,891 bytes (extracted 2026-08-12)"),
            ("`north.pmtiles`, the 17 northern provinces, z0 to z15", "244,404,745 bytes (2026-10-03)"),
            ("`cm-cr-terrain.pmtiles`, elevation as terrarium tiles, z12", "161,156,720 bytes"),
            ("label glyphs, Noto Sans (SIL OFL), four ranges: Latin, Latin extended, Thai, general punctuation and currency", "4 `.pbf` files"),
        ]),
        ("p", "`map_shell.py` is the one module that configures a map. Each map is drawn first as a Python-made SVG, which is what prints, what shows with scripting off and what shows while tiles arrive; MapLibre mounts over it in the same box. `data/basemap.json` with no `url` switches the tile layer off and leaves the SVG. The OpenStreetMap credit is configured visible on every map surface, as the ODbL asks."),
        ("p", "`map_ground.py` reads the same archive in stdlib Python (PMTiles v3 and MVT) to paint ground under share cards, plan GIFs and posters that Pillow draws. It returns geometry in longitude and latitude for the caller's own projection, draws roads in metres with a pixel floor, and treats polygon holes as holes, so the moat stays a ring. The credit is drawn into the pixels because a GIF travels without its page."),
    ]},
    {"id": "search", "th": "ค้นหา", "en": "Search", "blocks": [
        ("p", "The search box matches on the device. `assets/searchcore.js` is generated from a sibling `search-core` repo, which also holds a Python twin of the same rules; a parity script runs a few thousand queries through both. Rules: normalization (Thai marks are whitelisted, since vowels and tone marks are Unicode category Mn); bounded edit distance with no slack on very short tokens; a phonetic key for Thai homophone spellings and for Latin romanization variants; dictionary segmentation of Thai chunks, with no character n-grams, applied to the documents too; a thesaurus mined from the site's own shelf vocabularies and a Thai root-word dictionary (4,113 groups in `data/search_thesaurus.json` on 2026-10-11); and intent lifting, so \"cheap dentist open now\" becomes a noun and three constraints. Terms loosen by steps, and documents matching only some terms show only when none matches all."),
        ("p", "The index is shipped to the browser. On 2026-09-08 it was 25,582 rows and 1,563,679 bytes gzipped; `indexsplit_layer.py` trimmed coordinates and moved some fields to a second file aligned by position, 1,238,000 bytes. After the Overture fold the catalogue is 89,082 rows, which the module's note puts well over four megabytes before an answer; that figure has not been re-measured here. The public API at `/api/v1/places` answered in about 120 ms and the search box did not call it, per the module's 2026-09-08 note; moving to it trades offline-first for size, and that trade is open."),
        ("p", "`/find` is a separate search over every page of every site on the roster: SQLite FTS5 in D1, loaded by `fleetsearch/load.py` from a crawl of each site's build. A reload takes 6 to 7 minutes, during which D1 does not answer queries and `/find` returns errors in bursts."),
    ]},
    {"id": "incidents", "th": "เหตุขัดข้อง", "en": "Incidents", "blocks": [
        ("table", ("วันที่", "Date", "เหตุ", "What happened"), [
            ("2026-09-08", "A deploy mirrored a `docs/` holding only `cm/` and `data/` onto the bucket. `rclone sync` deleted the front page, `404.html`, both vendored libraries, the glyphs, all of `cr/` and the API index, and `motdang.net` answered 404 for its own front page. The 20,000-file floor passed, since `cm/` alone is 77,107 files. Result: `safety.py`, which asks whether a tree is the site and not whether it is large. Two days later, the `docs.next` swap."),
            ("2026-10-05", "A build died with `Errno 28` after the disk reached 213 MB free, and took other processes on the machine down with it. Result: `check_room()`."),
            ("2026-09-20 to 2026-10-05", "Half-edited code in the working tree failed 58 builds and gates. Result: the last-good-code rebuild, then builds from a commit."),
            ("2026-10-05 to 2026-10-10", "No server build finished. A sampler injected into a running build found about 90% of the time in one function. Result: one shared read, a 360-minute limit, a live-file check against the bucket instead of the laptop's `docs/`, and `build.py` must import before a hand-off is sent."),
            ("2026-10-10", "A stalled copy-back of the server's `docs/` to the Mac blocked a round and held a lock. Result: a 300-second idle timeout on every transfer, then removal of the copy-back."),
        ]),
    ]},
    {"id": "open", "th": "ค้างอยู่", "en": "Open items", "blocks": [
        ("ul", [
            "The `/find` reload crawls a local `docs/`. Builds now run on the server.",
            "D1 coordinates: 3,705 of an intended 76,847 rows carried a pin on 2026-09-21, after a D1 import returned `502` and locked the database for 25 minutes. Distance works where a row has one.",
            "The index shipped to the browser grows with the catalogue. The API is the alternative, and it costs offline-first.",
        ]),
    ]},
]


# ----------------------------------------------------------------------------- rendering

def inline(s):
    """Escape, then turn `code` into <code>."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(s, quote=False))


def bi(th, en):
    return ('<span class="bi"><span class="th" lang="th">%s</span>'
            '<span class="en" lang="en"><span class="th" lang="th"> · </span>%s</span></span>'
            % (html.escape(th, quote=False), html.escape(en, quote=False)))


CSS = """
.bn p,.bn li{line-height:1.65;max-width:68ch}
.bn h2{margin:2.2rem 0 .5rem}
.bn code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.88em;word-break:break-word}
.bn table{border-collapse:collapse;width:100%;max-width:60rem;margin:1rem 0}
.bn th,.bn td{text-align:left;padding:.5rem .65rem;border-bottom:1px solid var(--line,#e4d9cd);vertical-align:top}
.bn th{font-size:.86rem;font-weight:600;color:var(--muted,#8a7a62)}
.bn td:first-child{min-width:12rem}
.bn nav{margin:1rem 0 0;display:flex;flex-wrap:wrap;gap:.2rem .9rem;font-size:.92rem}
.bn .lede{font-size:1.06rem}
@media(max-width:640px){.bn th,.bn td{padding:.45rem .4rem;font-size:.92rem}}
"""


def block_html(b):
    kind = b[0]
    if kind == "p":
        return '<p lang="en">%s</p>' % inline(b[1])
    if kind == "ul":
        return '<ul lang="en">%s</ul>' % "".join("<li>%s</li>" % inline(x) for x in b[1])
    if kind == "ol":
        return '<ol lang="en">%s</ol>' % "".join("<li>%s</li>" % inline(x) for x in b[1])
    if kind == "table":
        head, rows = b[1], b[2]
        th = "".join("<th>%s</th>" % bi(head[i], head[i + 1]) for i in range(0, len(head), 2))
        trs = "".join("<tr>%s</tr>" % "".join("<td lang=\"en\">%s</td>" % inline(c) for c in r) for r in rows)
        return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, trs)
    raise ValueError(kind)


def body(sections=SECTIONS):
    out = ['<div class="bn">', "<h1>%s</h1>" % bi(*TITLE), '<p class="lede">%s</p>' % bi(*LEDE)]
    out.append("<nav>%s</nav>" % " ".join('<a href="#%s">%s</a>' % (s["id"], bi(s["th"], s["en"])) for s in sections))
    for s in sections:
        out.append('<section id="%s"><h2>%s</h2>%s</section>' % (s["id"], bi(s["th"], s["en"]),
                                                                  "".join(block_html(b) for b in s["blocks"])))
    out.append("</div>")
    return "\n".join(out)


def plain(sections=SECTIONS):
    """The same content as plain text: one paragraph per line, tables as one line per row."""
    out = ["%s · %s" % (TITLE[0], TITLE[1]), LEDE[1], ""]
    for s in sections:
        out += ["", "%s · %s" % (s["en"].upper(), s["th"]), ""]
        for b in s["blocks"]:
            if b[0] == "p":
                out += [b[1], ""]
            elif b[0] in ("ul", "ol"):
                out += ["%s %s" % ("-" if b[0] == "ul" else "%d." % (i + 1), x) for i, x in enumerate(b[1])] + [""]
            else:
                out += ["  %s  |  %s" % (r[0], r[1]) for r in b[2]] + [""]
    return "\n".join(out).rstrip() + "\n"
