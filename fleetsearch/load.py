#!/usr/bin/env python3
"""fleetsearch/load.py — put the crawled corpus into the search index.

    python3 fleetsearch/load.py --sql       # pages.jsonl → cache/fleetsearch/sql/*.sql
    python3 fleetsearch/load.py --local     # the same SQL → cache/fleetsearch/fleet.sqlite
    python3 fleetsearch/load.py --remote    # the same SQL → D1 (motdang-search), swapped in
    python3 fleetsearch/load.py             # all three

TWO WAYS TO LOAD, and the second one is the default now.

`--beside` builds `pages2` / `keys2` / `fts2` alongside the live tables and
renames them in at the end, so a reader mid-load keeps the previous index
whole. It is atomic, and it costs what atomicity costs here: two copies of a
660 MB database at once, and a search that answers nothing for as long as the
import runs.

`--in-place` writes the same rows straight over the live ones. Every insert is
keyed, so a row is replaced rather than duplicated, and rows the new crawl no
longer holds are deleted at the end. A reader mid-load sees a mix of yesterday's
rows and today's, which for a directory that changed by a few hundred pages is
a difference nobody can see — and the search keeps answering throughout.

MEASURED 2026-09-21, and it is why the default changed: a `--beside` reload
stalled on chunk 5, D1 answered `Authentication error [code: 10000]` and then
`internal error [code: 7500]` to every query it was given, `SELECT 1` included, and
motdang.net/find was down for 25 minutes. The database was holding 787 MB of
two indexes at the time. Dropping the half-built copy brought it back.

D1 takes the SQL through `wrangler d1 execute --remote --file`, one chunk at a
time. Cloudflare faults here are ordinary and transient — "Upstream service
unavailable", `{"D1_RESET_DO":true}` — so a chunk is retried five times with a
backoff that doubles from 20 seconds, and the load stops with nothing swapped
only if all five fail. It then says which chunk to resume from: because every
insert is keyed, `--from N` picks up where it stopped instead of starting the
whole load again.

**Every insert is OR REPLACE, and that is not decoration.** Cloudflare answered
one chunk with "Upstream service unavailable" after applying part of it, and
the plain retry then died on `UNIQUE constraint failed: pages2.id` — so a
transient network fault turned into a failed load. Keyed by id, a re-run of a
chunk now lands exactly where the first attempt did.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deboil import Deboil  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CACHE = REPO / "cache" / "fleetsearch"
PAGES = CACHE / "pages.jsonl"
SQL_DIR = CACHE / "sql"
LOCAL = CACHE / "fleet.sqlite"
PUBLISH = REPO / "publish"
DB_NAME = "motdang-search"

STMT_BYTES = 60_000      # D1 refuses a statement past ~100 KB (SQLITE_TOOBIG)
CHUNK_BYTES = 12_000_000
TOKENIZE = "unicode61 remove_diacritics 2 categories 'L* N* Co Mn Mc'"
RANK = "bm25(8.0, 1.0, 2.0, 0.0)"   # title, body, address, site (a filter, not a score)


def q(s) -> str:
    """One SQL string literal."""
    return "'" + str(s if s is not None else "").replace("\x00", "").replace("'", "''") + "'"


def schema(sfx: str, stamp: str) -> str:
    """The tables.

    Loading beside the live ones starts from nothing, so they are dropped and
    made fresh. Loading in place starts from tables that are answering
    queries: they are created only if missing, the index carries a fixed name
    because nothing is being renamed around it, and a column a later version
    added is put on by an ALTER that is allowed to fail — `IF NOT EXISTS` is
    not a thing SQLite offers for a column, and asking D1 first would cost a
    round trip to learn what the next statement learns anyway.
    """
    if not sfx:
        return f"""
CREATE TABLE IF NOT EXISTS pages(id INTEGER PRIMARY KEY, site TEXT NOT NULL, host TEXT NOT NULL,
  url TEXT NOT NULL, title TEXT NOT NULL, abstract TEXT NOT NULL DEFAULT '',
  lastmod TEXT NOT NULL, kb INTEGER NOT NULL, crumbs TEXT, thumb TEXT, rich TEXT);
CREATE INDEX IF NOT EXISTS ix_site ON pages(site);
CREATE TABLE IF NOT EXISTS keys(id INTEGER PRIMARY KEY, site TEXT NOT NULL, host TEXT NOT NULL,
  lastmod TEXT NOT NULL, title TEXT NOT NULL, lat REAL, lon REAL{KEYS_MORE});
CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(title_s, body_s, url_s, site_s,
  tokenize="{TOKENIZE}");
INSERT INTO fts(fts, rank) VALUES('rank', '{RANK}');
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS scheds(k INTEGER PRIMARY KEY, iv TEXT NOT NULL);
"""
    return f"""
DROP TABLE IF EXISTS pages{sfx};
DROP TABLE IF EXISTS keys{sfx};
DROP TABLE IF EXISTS fts{sfx};
DROP TABLE IF EXISTS meta{sfx};
DROP TABLE IF EXISTS scheds{sfx};
CREATE TABLE pages{sfx}(id INTEGER PRIMARY KEY, site TEXT NOT NULL, host TEXT NOT NULL,
  url TEXT NOT NULL, title TEXT NOT NULL, abstract TEXT NOT NULL DEFAULT '',
  lastmod TEXT NOT NULL, kb INTEGER NOT NULL, crumbs TEXT, thumb TEXT, rich TEXT);
CREATE INDEX ix_{stamp}_site ON pages{sfx}(site);
-- The narrow twin. Sorting by date or name, filtering by date, and counting an
-- answer by site touch up to a thousand scattered rows; read from `pages`
-- those are fat rows (title + abstract + url) and the broadest query took nine
-- seconds. A covering index on `pages` did not fix it — for a rowid table
-- SQLite prefers the primary key and reads the fat row anyway. So the keys
-- live in their own table, ~10 MB, and only the rows that survive the sort are
-- fetched whole.
CREATE TABLE keys{sfx}(id INTEGER PRIMARY KEY, site TEXT NOT NULL, host TEXT NOT NULL,
  lastmod TEXT NOT NULL, title TEXT NOT NULL, lat REAL, lon REAL{KEYS_MORE});
CREATE VIRTUAL TABLE fts{sfx} USING fts5(title_s, body_s, url_s, site_s, tokenize="{TOKENIZE}");
INSERT INTO fts{sfx}(fts{sfx}, rank) VALUES('rank', '{RANK}');
CREATE TABLE meta{sfx}(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE scheds{sfx}(k INTEGER PRIMARY KEY, iv TEXT NOT NULL);
"""


# Columns added after the first release. Applied one at a time in place, and a
# failure is the answer "it is already there" rather than a fault.
MIGRATIONS = ["ALTER TABLE keys ADD COLUMN lat REAL",
              "ALTER TABLE keys ADD COLUMN lon REAL",
              "ALTER TABLE keys ADD COLUMN kind TEXT",
              "ALTER TABLE keys ADD COLUMN sec TEXT",
              "ALTER TABLE keys ADD COLUMN has INTEGER NOT NULL DEFAULT 0",
              "ALTER TABLE keys ADD COLUMN sk INTEGER",
              "ALTER TABLE keys ADD COLUMN evn TEXT",
              "ALTER TABLE keys ADD COLUMN evu TEXT",
              "ALTER TABLE keys ADD COLUMN score INTEGER NOT NULL DEFAULT 0",
              "ALTER TABLE keys ADD COLUMN evc INTEGER NOT NULL DEFAULT 0",
              "ALTER TABLE pages ADD COLUMN crumbs TEXT",
              "ALTER TABLE pages ADD COLUMN thumb TEXT",
              "ALTER TABLE pages ADD COLUMN rich TEXT"]

# What a result row can be filtered on, as bits of keys.has. fleetsearch.js
# carries the same table (HAS); the two must agree.
HAS = {"photo": 1, "contact": 2, "toilet": 4, "events": 8, "hours": 16, "map": 32}
KEYS_MORE = (", kind TEXT, sec TEXT, has INTEGER NOT NULL DEFAULT 0, sk INTEGER,"
             " evn TEXT, evu TEXT, score INTEGER NOT NULL DEFAULT 0, evc INTEGER NOT NULL DEFAULT 0")
THUMBS = CACHE / "thumbs.json"
FOREVER = "9999-12-31"


def bangkok_today() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=7)).strftime("%Y-%m-%d")


def upcoming(events: list, today: str) -> tuple[list, str | None, str | None]:
    """The events still to come, the next date any of them falls on, and the
    last date any of them runs to. A weekly event with no end runs on."""
    t = date.fromisoformat(today)
    keep, nexts, lasts = [], [], []
    for e in events or []:
        try:
            d = date.fromisoformat(e["d"])
        except (KeyError, ValueError):
            continue
        if e.get("w"):
            until = e.get("u") or FOREVER
            if until < today:
                continue
            start = max(d, t)
            nxt = min(start + timedelta(days=(wd - start.weekday()) % 7) for wd in e["w"])
            if nxt.isoformat() > until:
                continue
            keep.append(e)
            nexts.append(nxt.isoformat())
            lasts.append(until)
        elif e["d"] >= today:
            keep.append(e)
            nexts.append(e["d"])
            lasts.append(e["d"])
    order = sorted(range(len(keep)), key=lambda i: nexts[i])
    return [keep[i] for i in order][:4], (min(nexts) if nexts else None), (max(lasts) if lasts else None)


def derive(r: dict, thumbs: dict, cells: set, scheds: dict, today: str) -> dict:
    """The filterable and displayable facts of one row, from what the crawler
    read and what thumbs.py drew."""
    from thumbs import cell_of
    rich = dict(r.get("rich") or {})
    has, thumb = 0, ""
    pic = thumbs.get(r.get("img") or "")
    if pic:
        thumb = f"p/{pic}"
        has |= HAS["photo"]
    if r.get("lat") is not None:
        hx, hy, _, _ = cell_of(r["lat"], r["lon"])
        if f"{hx}_{hy}" in cells:
            has |= HAS["map"]
            if not thumb:
                thumb = f"g/{hx}_{hy}"
    if not pic:
        rich.pop("credit", None)
    if rich.get("ways"):
        has |= HAS["contact"]
    tl = rich.get("toilet")
    if isinstance(tl, list) and tl and tl[0] in ("r", "s", "h"):    # "n" is one nearby, not its own
        has |= HAS["toilet"]
    ev, evn, evu = upcoming(rich.pop("ev", None), today)
    # events and series listed at the place, coming and gone (the event ledger);
    # fleetsearch.js weighs best-match by it
    evc = rich.pop("evc", 0)
    evc = evc if isinstance(evc, int) and evc > 0 else 0
    if ev:
        rich["ev"] = ev
        has |= HAS["events"]
    sk = None
    sched = rich.pop("sched", None)
    if sched is not None:
        has |= HAS["hours"]
        if sched:
            iv = json.dumps(sched, separators=(",", ":"))
            sk = scheds.setdefault(iv, len(scheds))
    if r.get("items"):
        rich["items"] = r["items"]
    crumbs = r.get("crumbs") or []
    sec = " › ".join(c[0] for c in crumbs[:2])
    score = (2 * bool(has & HAS["photo"]) + len(rich.get("ways") or []) + 2 * bool(has & HAS["toilet"])
             + 2 * bool(ev) + bool(has & HAS["hours"]) + min(len(rich.get("fac") or []), 5)
             + bool(has & HAS["map"]) + min(evc, 5))
    return {"has": has, "thumb": thumb, "rich": rich, "sk": sk, "evn": evn, "evu": evu,
            "sec": sec, "kind": r.get("kind") or "page", "score": score, "crumbs": crumbs,
            "evc": evc}


STRIP = 5


def strip_item(r: dict, d: dict) -> tuple:
    """(rank key, [name, url, thumb, reading, scene, lat?, lon?]) for one place, as a list's strip shows it:
    pictures first, then drawings, then the fullest record."""
    rich = d["rich"]
    name = r["title"].split(" — ", 1)[0].strip()[:60]
    rd = (rich.get("rd") or ["", ""])[1]
    th = d["thumb"] or ""
    key = (0 if th.startswith("p/") else 1 if rich.get("sc") else 2, -d["score"])
    item = [name, r["url"], th, rd, rich.get("sc") or ""]
    if th.startswith("g/"):                 # a map cell: the strip draws the pin, as the row does
        item += [round(r["lat"], 5), round(r["lon"], 5)]
    return key, item


def strip_of(r: dict, by_url: dict) -> list:
    """A list page's best few places with their pictures, from its own items (crawl.py members)."""
    base = r["url"].split("/", 3)
    base = "/".join(base[:3]) + "/"
    got = [by_url[base + m] for m in r["members"] if base + m in by_url]
    got = [x for x in got if x[1][2]]
    got.sort(key=lambda x: x[0])            # stable: the list's own order breaks ties
    return [x[1] for x in got[:STRIP]]


def write_sql(sfx: str, stamp: str) -> list[Path]:
    """pages.jsonl → numbered SQL chunks. 000 holds the schema; the last holds meta."""
    SQL_DIR.mkdir(parents=True, exist_ok=True)
    for old in SQL_DIR.glob("*.sql"):
        old.unlink()
    files = []
    n = 0
    pinned = 0
    sites = {}
    buf = [schema(sfx, stamp)]
    size = len(buf[0])
    prow, frow, krow = [], [], []
    # Track all three statements, not just fts: the pages row carries abstract
    # and the rich JSON and is the fattest, so gating the flush on fts bytes
    # alone let the pages INSERT run past D1's per-statement ceiling
    # (162 KB seen 2026-09-26 → SQLITE_TOOBIG). Flush on whichever grows first.
    pbytes = fbytes = kbytes = 0

    def flush_rows():
        nonlocal prow, frow, krow, size, pbytes, fbytes, kbytes
        if prow:
            s1 = f"INSERT OR REPLACE INTO pages{sfx}(id,site,host,url,title,abstract,lastmod,kb,crumbs,thumb,rich) VALUES\n" + ",\n".join(prow) + ";\n"
            s2 = f"INSERT OR REPLACE INTO fts{sfx}(rowid,title_s,body_s,url_s,site_s) VALUES\n" + ",\n".join(frow) + ";\n"
            s3 = f"INSERT OR REPLACE INTO keys{sfx}(id,site,host,lastmod,title,lat,lon,kind,sec,has,sk,evn,evu,score,evc) VALUES\n" + ",\n".join(krow) + ";\n"
            buf.append(s1); buf.append(s2); buf.append(s3)
            size += len(s1) + len(s2) + len(s3)
            prow, frow, krow = [], [], []
            pbytes = fbytes = kbytes = 0

    def flush_file():
        nonlocal buf, size
        p = SQL_DIR / f"{len(files):03d}.sql"
        p.write_text("".join(buf), encoding="utf-8")
        files.append(p)
        buf, size = [], 0

    try:
        th = json.loads(THUMBS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        th = {}
        print(f"  no {THUMBS.name}: rows go without pictures or maps "
              f"(python3 fleetsearch/thumbs.py makes them)", file=sys.stderr)
    thumbs, cells = th.get("pics") or {}, set(th.get("cells") or [])
    scheds, sec_en = {}, {}
    today = bangkok_today()
    tally = {k: 0 for k in HAS}
    nul = lambda v: "NULL" if v is None else q(v)          # noqa: E731
    js = lambda v: q(json.dumps(v, ensure_ascii=False, separators=(",", ":"))) if v else "NULL"  # noqa: E731
    # Templates out before anything is written: counted over the whole corpus
    # first, then taken out of each row (deboil.py says why).
    db = Deboil(REPO / "docs" / "data" / "search_thesaurus.json")
    by_url = {}                    # url → what a list's picture strip shows of it
    with open(PAGES, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            db.count(r)
            if r.get("kind") == "place":
                by_url[r["url"]] = strip_item(r, derive(r, thumbs, cells, {}, today))
    db.prune()
    with open(PAGES, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            r["title_s"], r["body_s"] = db.apply(r)
            n += 1
            sites[r["site"]] = sites.get(r["site"], 0) + 1
            pinned += r.get("lat") is not None
            d = derive(r, thumbs, cells, scheds, today)
            if r.get("members"):
                pv = strip_of(r, by_url)
                if pv:
                    d["rich"]["pv"] = pv
            if d["sec"] and d["sec"] not in sec_en and any(c[2] for c in d["crumbs"][:2]):
                sec_en[d["sec"]] = " › ".join(c[2] or c[0] for c in d["crumbs"][:2])
            for k, bit in HAS.items():
                tally[k] += bool(d["has"] & bit)
            prow.append(f"({n},{q(r['site'])},{q(r['host'])},{q(r['url'])},{q(r['title'])},{q(r['abstract'])},"
                        f"{q(r['lastmod'])},{int(r['kb'])},{js(d['crumbs'])},{nul(d['thumb'] or None)},{js(d['rich'])})")
            pbytes += len(prow[-1].encode("utf-8"))
            ll = (f"{r['lat']:.6f},{r['lon']:.6f}" if r.get("lat") is not None else "NULL,NULL")
            krow.append(f"({n},{q(r['site'])},{q(r['host'])},{q(r['lastmod'])},{q(r['title'])},{ll},"
                        f"{q(d['kind'])},{q(d['sec'])},{d['has']},{'NULL' if d['sk'] is None else d['sk']},"
                        f"{nul(d['evn'])},{nul(d['evu'])},{d['score']},{d['evc']})")
            kbytes += len(krow[-1].encode("utf-8"))
            site_s = f"{r['host']} {r['site']} {r['host']}/{r['site']}"
            frow.append(f"({n},{q(r['title_s'])},{q(r['body_s'])},{q(r['url_s'])},{q(site_s)})")
            fbytes += len(frow[-1].encode("utf-8"))
            if max(pbytes, fbytes, kbytes) >= STMT_BYTES:
                flush_rows()
            if size >= CHUNK_BYTES:
                flush_file()
    flush_rows()
    gen = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # The week schedules the rows point at by sk: minute-of-week intervals,
    # Monday 00:00 = 0, in Bangkok time — build_open_lamps.py's own shape.
    buf.append(f"DELETE FROM scheds{sfx};\n")
    rows = [f"({k},{q(iv)})" for iv, k in scheds.items()]
    for i in range(0, len(rows), 400):
        buf.append(f"INSERT OR REPLACE INTO scheds{sfx}(k,iv) VALUES\n" + ",\n".join(rows[i:i + 400]) + ";\n")
    buf.append(f"INSERT OR REPLACE INTO meta{sfx}(k,v) VALUES ('generated',{q(gen)}),('pages',{q(n)}),"
               f"('sites',{q(len(sites))}),('thumbs',{q(th.get('prefix') or '')});\n")
    # sec_en — every section's English, one JSON map — is ~160 KB whole, past
    # D1's per-statement ceiling (SQLITE_TOOBIG, 2026-09-26). It travels in
    # ordered ~45 KB pieces the Worker joins back (aux() in fleetsearch.js).
    # Split by characters, never bytes, so no multibyte code point is torn.
    buf.append(f"DELETE FROM meta{sfx} WHERE k = 'sec_en' OR k LIKE 'sec_en:%';\n")
    blob = json.dumps(sec_en, ensure_ascii=False, separators=(",", ":"))
    STEP = 15000  # chars; Thai is 3 bytes, so a piece stays well under STMT_BYTES
    parts = [blob[i:i + STEP] for i in range(0, len(blob), STEP)] or [""]
    for j, part in enumerate(parts):
        buf.append(f"INSERT OR REPLACE INTO meta{sfx}(k,v) VALUES ('sec_en:{j:03d}',{q(part)});\n")
    flush_file()
    (CACHE / "load.json").write_text(json.dumps({"generated": gen, "pages": n, "sites": sites,
                                                 "pinned": pinned, "chunks": len(files),
                                                 "has": tally, "schedules": len(scheds)},
                                                ensure_ascii=False, indent=1))
    print(f"{n} pages, {len(sites)} sites, {pinned} with a pin → {len(files)} chunks in {SQL_DIR}",
          file=sys.stderr)
    print("  " + " · ".join(f"{k} {v}" for k, v in tally.items()) + f" · {len(scheds)} schedules",
          file=sys.stderr)
    return files


def load_local(files: list[Path], sfx: str):
    if LOCAL.exists():
        LOCAL.unlink()
    con = sqlite3.connect(LOCAL)
    t = time.time()
    for p in files:
        con.executescript(p.read_text(encoding="utf-8"))
    if sfx:
        con.executescript(swap_sql(sfx, con))
    else:
        for table, col in (("keys", "id"), ("fts", "rowid")):
            con.execute(f"DELETE FROM {table} WHERE {col} > (SELECT max(id) FROM pages)")
    con.commit()
    n = con.execute("SELECT count(*) FROM pages").fetchone()[0]
    m = con.execute("SELECT count(*) FROM fts WHERE fts MATCH '\"เชียงใหม่\"'").fetchone()[0]
    con.close()
    print(f"local twin {LOCAL}: {n} pages, เชียงใหม่ on {n and m} pages, {time.time()-t:.0f}s", file=sys.stderr)


def swap_sql(sfx: str, con=None) -> str:
    """Rename the freshly built tables into place. Live tables, when they
    exist, go to *_old and are dropped afterwards."""
    if con is not None:
        have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table')")}
    else:
        have = remote_tables()
    tables = ("pages", "keys", "fts", "meta", "scheds")
    out = [f"DROP TABLE IF EXISTS {t}_old;" for t in tables]
    for t in tables:
        if t in have:
            out.append(f"ALTER TABLE {t} RENAME TO {t}_old;")
        out.append(f"ALTER TABLE {t}{sfx} RENAME TO {t};")
    out += [f"DROP TABLE IF EXISTS {t}_old;" for t in tables]
    return "\n".join(out) + "\n"


def wrangler(*args, timeout=1800) -> subprocess.CompletedProcess:
    cmd = ["npx", "--no-install", "wrangler", "d1", "execute", DB_NAME, "--remote", "-y", *args]
    return subprocess.run(cmd, cwd=PUBLISH, capture_output=True, text=True, timeout=timeout)


def remote_tables() -> set:
    r = wrangler("--json", "--command", "SELECT name FROM sqlite_master WHERE type='table'")
    if r.returncode:
        raise SystemExit(f"wrangler: {r.stderr[-800:]}")
    doc = json.loads(r.stdout[r.stdout.index("["):])
    return {row["name"] for row in doc[0]["results"]}


def remote_count(sql: str) -> int:
    r = wrangler("--json", "--command", sql)
    if r.returncode:
        raise SystemExit(f"wrangler: {r.stderr[-800:]}")
    doc = json.loads(r.stdout[r.stdout.index("["):])
    return int(list(doc[0]["results"][0].values())[0])


RETRIES = 5
BACKOFF = 20


def migrate():
    """Columns a later version added, onto tables that already exist."""
    for stmt in MIGRATIONS:
        r = wrangler("--command", stmt)
        state = "added" if r.returncode == 0 else "already there"
        print(f"  {stmt.split('ADD COLUMN ')[-1]:<12} {state}", file=sys.stderr)


def load_remote(files: list[Path], sfx: str, expect: int, start: int = 0):
    t0 = time.time()
    if not sfx and start == 0:
        migrate()
    for i, p in enumerate(files):
        if i < start:
            continue
        for attempt in range(RETRIES):
            t = time.time()
            r = wrangler("--file", str(p))
            if r.returncode == 0:
                print(f"  {p.name} {p.stat().st_size//1_000_000:3d} MB  {time.time()-t:5.0f}s  ({i+1}/{len(files)})", file=sys.stderr)
                break
            wait = BACKOFF * 2 ** attempt
            print(f"  {p.name} attempt {attempt+1} failed, {wait}s then again: {r.stderr[-300:].strip()}",
                  file=sys.stderr)
            time.sleep(wait)
        else:
            raise SystemExit(f"stopped at {p.name}; nothing swapped — the live index is untouched. "
                             f"Resume with: python3 fleetsearch/load.py --remote --from {i}")
    if sfx:
        # A chunk that fails part-way and is retried inserts its rows twice. The
        # id columns catch that on pages and keys; the FTS table has no key of
        # its own, so it is counted too — a doubled index would still answer,
        # wrongly, and nothing about the pages count would look off.
        for t in ("pages", "keys", "fts"):
            n = remote_count(f"SELECT count(*) FROM {t}{sfx}")
            if n != expect:
                raise SystemExit(f"{t}{sfx} holds {n}, expected {expect}; nothing swapped")
        r = wrangler("--command", swap_sql(sfx))
        if r.returncode:
            raise SystemExit(f"swap failed: {r.stderr[-800:]}")
    else:
        # In place the ids run 1..expect, so anything above that is a page the
        # last crawl held and this one did not. Deleted last: until it is, the
        # index answers with a few stale rows, which beats answering nothing.
        for t in ("pages", "keys", "fts"):
            col = "rowid" if t == "fts" else "id"
            r = wrangler("--command", f"DELETE FROM {t} WHERE {col} > {expect}")
            if r.returncode:
                print(f"  {t}: stale rows above {expect} are still there — {r.stderr[-200:].strip()}",
                      file=sys.stderr)
    live = remote_count("SELECT count(*) FROM pages")
    hits = remote_count("SELECT count(*) FROM fts WHERE fts MATCH '\"เชียงใหม่\"'")
    pins = remote_count("SELECT count(*) FROM keys WHERE lat IS NOT NULL")
    print(f"D1 {DB_NAME}: {live} pages live, {pins} with a pin, เชียงใหม่ on {hits}, "
          f"{(time.time()-t0)/60:.0f} min", file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", action="store_true")
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--remote", action="store_true")
    ap.add_argument("--beside", action="store_true",
                    help="build a second copy and swap it in (atomic; the search is down meanwhile)")
    ap.add_argument("--from", dest="start", type=int, default=0,
                    help="resume the remote load at this chunk (the number a failure printed)")
    a = ap.parse_args(argv)
    if not (a.sql or a.local or a.remote):
        a.sql = a.local = a.remote = True
    if a.start and a.sql:
        raise SystemExit("--from resumes a load; regenerating the SQL would renumber the chunks")
    sfx = "2" if a.beside else ""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    if a.sql:
        files = write_sql(sfx, stamp)
    else:
        files = sorted(SQL_DIR.glob("*.sql"))
        if not files:
            raise SystemExit("no SQL chunks; run --sql first")
    expect = json.loads((CACHE / "load.json").read_text())["pages"]
    if a.local:
        load_local(files, sfx)
    if a.remote:
        load_remote(files, sfx, expect, a.start)
    vocab(a.local, a.remote)
    return 0


# The index's own word list, for the search's near-spelling step
# (publish/fleetsearch.js nearSpell). fts5vocab is a view onto the FTS table
# by name, so it holds no rows of its own and follows `fts` through a swap.
VOCAB_DDL = "CREATE VIRTUAL TABLE IF NOT EXISTS fts_v USING fts5vocab(fts, row)"


def vocab(local: bool, remote: bool):
    if local and LOCAL.exists():
        con = sqlite3.connect(LOCAL)
        con.execute(VOCAB_DDL)
        con.commit()
        con.close()
    if remote:
        r = wrangler("--command", VOCAB_DDL)
        if r.returncode:
            print(f"  fts_v not made: {r.stderr[-200:].strip()}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
